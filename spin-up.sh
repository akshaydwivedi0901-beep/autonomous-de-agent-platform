#!/bin/bash
# ============================================================
# SPIN UP — Full AWS Platform for Testing
# Usage: bash spin-up.sh
# Cost: ~$0.02-0.05/hour on t3.micro SPOT
# Always run tear-down.sh after testing!
# ============================================================

set -e   # exit on any error

# ── Config ──────────────────────────────────────────────────
AWS_REGION="us-east-1"
ECR_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="ai-agent"
CLUSTER_NAME="ai-agent-cluster"
NAMESPACE="default"
IMAGE_TAG="test-$(date +%Y%m%d%H%M%S)"
TERRAFORM_DIR="./terraform"

# ── Colors ──────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()    { echo -e "${GREEN}[$(date +%H:%M:%S)] $1${NC}"; }
warn()   { echo -e "${YELLOW}[$(date +%H:%M:%S)] $1${NC}"; }
error()  { echo -e "${RED}[$(date +%H:%M:%S)] ERROR: $1${NC}"; exit 1; }

# ── Pre-flight checks ────────────────────────────────────────
log "Running pre-flight checks..."
command -v terraform >/dev/null 2>&1 || error "terraform not found. Install: https://developer.hashicorp.com/terraform/install"
command -v aws >/dev/null 2>&1       || error "aws CLI not found"
command -v kubectl >/dev/null 2>&1   || error "kubectl not found"
command -v docker >/dev/null 2>&1    || error "docker not found"

# Check AWS credentials
aws sts get-caller-identity >/dev/null 2>&1 || error "AWS credentials not configured. Run: aws configure"

log "Pre-flight checks passed ✅"

# ── Step 1: Terraform infrastructure ────────────────────────
log "Step 1/6: Provisioning AWS infrastructure with Terraform..."
cd $TERRAFORM_DIR

terraform init -upgrade -input=false
terraform apply -auto-approve -input=false \
  -var="aws_region=$AWS_REGION" \
  -var="node_instance_type=t3.micro"

ECR_URL=$(terraform output -raw ecr_repository_url)
CLUSTER=$(terraform output -raw cluster_name)
KUBECTL_CMD=$(terraform output -raw kubeconfig_command)

cd ..

log "Infrastructure ready ✅ (ECR: $ECR_URL)"

# ── Step 2: Configure kubectl ────────────────────────────────
log "Step 2/6: Configuring kubectl..."
eval $KUBECTL_CMD

# Wait for nodes to be ready
log "Waiting for EKS nodes to be ready (may take 2-3 minutes)..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

log "Nodes ready ✅"

# ── Step 3: Create K8s secrets ──────────────────────────────
log "Step 3/6: Creating Kubernetes secrets..."

# Check required env vars
REQUIRED_VARS=(GROQ_API_KEY SNOWFLAKE_USER SNOWFLAKE_PASSWORD SNOWFLAKE_ACCOUNT SNOWFLAKE_WAREHOUSE SNOWFLAKE_DATABASE SNOWFLAKE_SCHEMA SNOWFLAKE_ROLE API_KEY)
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    error "Environment variable $var is not set. Export it before running this script."
  fi
done

kubectl create secret generic groq-secret \
  --from-literal=GROQ_API_KEY="$GROQ_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic snowflake-secret \
  --from-literal=SNOWFLAKE_USER="$SNOWFLAKE_USER" \
  --from-literal=SNOWFLAKE_PASSWORD="$SNOWFLAKE_PASSWORD" \
  --from-literal=SNOWFLAKE_ACCOUNT="$SNOWFLAKE_ACCOUNT" \
  --from-literal=SNOWFLAKE_WAREHOUSE="$SNOWFLAKE_WAREHOUSE" \
  --from-literal=SNOWFLAKE_DATABASE="$SNOWFLAKE_DATABASE" \
  --from-literal=SNOWFLAKE_SCHEMA="$SNOWFLAKE_SCHEMA" \
  --from-literal=SNOWFLAKE_ROLE="$SNOWFLAKE_ROLE" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic app-secret \
  --from-literal=API_KEY="$API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

log "Secrets created ✅"

# ── Step 4: Build & push Docker image ───────────────────────
log "Step 4/6: Building and pushing Docker image..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URL

# Build
cd agentic-platform
docker build \
  --label "git-commit=$(git rev-parse --short HEAD 2>/dev/null || echo 'local')" \
  --label "build-time=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -t $ECR_URL:$IMAGE_TAG \
  -t $ECR_URL:latest \
  -f docker/Dockerfile .
cd ..

# Push
docker push $ECR_URL:$IMAGE_TAG
docker push $ECR_URL:latest

log "Image pushed ✅ ($ECR_URL:$IMAGE_TAG)"

# ── Step 5: Deploy to EKS ───────────────────────────────────
log "Step 5/6: Deploying to EKS..."

# Apply ChromaDB PVC
kubectl apply -f agentic-platform/k8s/chroma-pvc.yaml

# Apply Redis
kubectl apply -f agentic-platform/k8s/redis-deployment.yaml

# Update image in deployment and apply
sed "s|image:.*ai-agent:.*|image: $ECR_URL:$IMAGE_TAG|g" \
  agentic-platform/k8s/deployment.yml | kubectl apply -f -

kubectl apply -f agentic-platform/k8s/service.yaml

# Wait for deployment
log "Waiting for deployment to be ready..."
kubectl rollout status deployment/ai-agent --timeout=300s

# Get service URL
log "Waiting for LoadBalancer IP..."
for i in {1..30}; do
  EXTERNAL_IP=$(kubectl get svc ai-agent-service \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
  if [ -n "$EXTERNAL_IP" ]; then
    break
  fi
  sleep 10
  echo "  Still waiting... ($i/30)"
done

log "Deployment ready ✅"

# ── Step 6: Run smoke tests ──────────────────────────────────
log "Step 6/6: Running smoke tests..."

# Wait for health check
sleep 15
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  http://$EXTERNAL_IP/health || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
  log "Health check passed ✅"
else
  warn "Health check returned HTTP $HEALTH_STATUS — checking logs..."
  kubectl logs -l app=ai-agent --tail=30
fi

# Test the execute endpoint
log "Testing execute endpoint..."
RESPONSE=$(curl -s -X POST \
  http://$EXTERNAL_IP/api/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"question": "how many orders were placed in 1995?", "environment": "prod"}' \
  || echo '{"error": "curl failed"}')

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q "EXPLAINED\|RETRY"; then
  log "Execute endpoint working ✅"
else
  warn "Execute endpoint returned unexpected response"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  Platform is running on AWS!"
echo "============================================================"
echo "  API URL:    http://$EXTERNAL_IP"
echo "  Health:     http://$EXTERNAL_IP/health"
echo "  Execute:    POST http://$EXTERNAL_IP/api/v1/execute"
echo "  Image tag:  $IMAGE_TAG"
echo ""
echo "  ⚠️  IMPORTANT: Run tear-down.sh when done to stop billing!"
echo "  Estimated cost: ~\$0.02-0.05/hour"
echo "============================================================"

# Save state for tear-down
cat > .platform-state << EOF
CLUSTER_NAME=$CLUSTER_NAME
ECR_URL=$ECR_URL
IMAGE_TAG=$IMAGE_TAG
EXTERNAL_IP=$EXTERNAL_IP
SPUN_UP_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

log "State saved to .platform-state"