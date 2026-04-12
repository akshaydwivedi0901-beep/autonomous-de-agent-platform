#!/bin/bash
# ============================================================
# TEAR DOWN — Destroy all AWS resources
# Usage: bash tear-down.sh
# Run this after every testing session to stop all billing
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)] $1${NC}"; }

# ── Read saved state ─────────────────────────────────────────
if [ -f .platform-state ]; then
  source .platform-state
  log "Tearing down platform spun up at: $SPUN_UP_AT"
else
  warn "No .platform-state found — running full Terraform destroy anyway"
fi

# ── Confirmation ─────────────────────────────────────────────
echo ""
echo "============================================================"
warn "  This will DESTROY all AWS resources:"
echo "  - EKS cluster and all nodes"
echo "  - VPC, subnets, internet gateway"
echo "  - All Kubernetes workloads"
echo ""
warn "  ECR repository and images will be KEPT"
warn "  (ECR costs ~\$0 when not actively pulling)"
echo "============================================================"
echo ""
read -p "Are you sure? Type 'destroy' to confirm: " CONFIRM

if [ "$CONFIRM" != "destroy" ]; then
  log "Cancelled."
  exit 0
fi

# ── Step 1: Delete K8s resources first (clean shutdown) ──────
log "Step 1/3: Cleaning up Kubernetes resources..."

if kubectl cluster-info >/dev/null 2>&1; then
  kubectl delete deployment ai-agent redis --ignore-not-found=true
  kubectl delete service ai-agent-service redis --ignore-not-found=true
  kubectl delete pvc chroma-pvc --ignore-not-found=true
  kubectl delete secret groq-secret snowflake-secret app-secret --ignore-not-found=true
  log "Kubernetes resources deleted ✅"
else
  warn "kubectl not configured or cluster already gone — skipping K8s cleanup"
fi

# ── Step 2: Terraform destroy ────────────────────────────────
log "Step 2/3: Destroying AWS infrastructure with Terraform..."
cd terraform

terraform destroy -auto-approve -input=false \
  -target=aws_eks_node_group.main \
  -target=aws_eks_cluster.main \
  -target=aws_subnet.public \
  -target=aws_route_table_association.public \
  -target=aws_route_table.public \
  -target=aws_internet_gateway.igw \
  -target=aws_vpc.main \
  -target=aws_iam_role_policy_attachment.worker_node \
  -target=aws_iam_role_policy_attachment.cni \
  -target=aws_iam_role_policy_attachment.ecr_readonly \
  -target=aws_iam_role_policy_attachment.ebs_csi \
  -target=aws_iam_role.eks_node \
  -target=aws_iam_role_policy_attachment.eks_cluster_policy \
  -target=aws_iam_role.eks_cluster

log "AWS infrastructure destroyed ✅"
cd ..

# ── Step 3: Clean up local state ─────────────────────────────
log "Step 3/3: Cleaning up local state..."
rm -f .platform-state
kubectl config delete-context $(kubectl config current-context 2>/dev/null) 2>/dev/null || true

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "============================================================"
log "  Tear-down complete! All AWS resources destroyed."
echo "  Billing has stopped (except ECR which costs ~\$0)"
echo ""
echo "  To run locally: docker-compose up --build"
echo "  To spin up AWS again: bash spin-up.sh"
echo "============================================================"