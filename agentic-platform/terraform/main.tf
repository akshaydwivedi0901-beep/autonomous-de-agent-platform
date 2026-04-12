terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5"

  # Uncomment to store state in S3 (recommended for team use)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "agentic-platform/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

# ============================================================
# VARIABLES
# ============================================================
variable "aws_region" {
  default = "us-east-1"
}

variable "project" {
  default = "agentic-platform"
}

variable "cluster_name" {
  default = "ai-agent-cluster"
}

# Cost-optimised: t3.micro for free tier testing
# Change to t3.small for production (enables HPA)
variable "node_instance_type" {
  default = "t3.micro"
}

variable "node_desired" {
  default = 1
  description = "Keep at 1 for free tier — only scale up when load testing"
}

# ============================================================
# ECR — always keep, costs ~$0 when not actively pushing
# ============================================================
resource "aws_ecr_repository" "ai_agent" {
  name                 = "ai-agent"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  # Auto-delete old images to stay under free tier
  lifecycle {
    prevent_destroy = false
  }

  tags = { Project = var.project }
}

resource "aws_ecr_lifecycle_policy" "ai_agent" {
  repository = aws_ecr_repository.ai_agent.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 3 images only"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 3
      }
      action = { type = "expire" }
    }]
  })
}

# ============================================================
# VPC — minimal: 2 public subnets, 1 IGW, no NAT (saves $32/mo)
# ============================================================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "${var.project}-vpc", Project = var.project }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project}-igw", Project = var.project }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = ["${var.aws_region}a", "${var.aws_region}b"][count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                        = "${var.project}-subnet-${count.index}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
    Project                                     = var.project
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "${var.project}-rt", Project = var.project }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ============================================================
# IAM — EKS Cluster Role
# ============================================================
resource "aws_iam_role" "eks_cluster" {
  name = "${var.project}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = { Project = var.project }
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

# ============================================================
# IAM — EKS Node Role
# ============================================================
resource "aws_iam_role" "eks_node" {
  name = "${var.project}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = { Project = var.project }
}

resource "aws_iam_role_policy_attachment" "worker_node" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "cni" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

# ============================================================
# EKS CLUSTER
# ============================================================
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = aws_subnet.public[*].id
    endpoint_public_access  = true
    endpoint_private_access = false
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]

  tags = { Project = var.project }
}

# ============================================================
# EKS NODE GROUP — ephemeral testing config
# ============================================================
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project}-nodes"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.public[*].id

  scaling_config {
    desired_size = var.node_desired
    max_size     = 2
    min_size     = 0    # can scale to 0 when not testing
  }

  instance_types = [var.node_instance_type]

  # Use spot instances for testing — 70% cheaper than on-demand
  # Remove capacity_type = "SPOT" for production stability
  capacity_type = "SPOT"

  depends_on = [
    aws_iam_role_policy_attachment.worker_node,
    aws_iam_role_policy_attachment.cni,
    aws_iam_role_policy_attachment.ecr_readonly,
    aws_iam_role_policy_attachment.ebs_csi,
  ]

  tags = { Project = var.project }
}

# ============================================================
# OUTPUTS
# ============================================================
output "ecr_repository_url" {
  value       = aws_ecr_repository.ai_agent.repository_url
  description = "ECR URL for pushing Docker images"
}

output "cluster_name" {
  value       = aws_eks_cluster.main.name
  description = "EKS cluster name for kubectl config"
}

output "cluster_endpoint" {
  value       = aws_eks_cluster.main.endpoint
  description = "EKS API server endpoint"
}

output "kubeconfig_command" {
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
  description = "Run this to configure kubectl"
}
