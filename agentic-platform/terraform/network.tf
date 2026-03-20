# =========================
# VPC
# =========================
resource "aws_vpc" "eks_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "eks-vpc"
  }
}

# =========================
# INTERNET GATEWAY
# =========================
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.eks_vpc.id

  tags = {
    Name = "eks-igw"
  }
}

# =========================
# PUBLIC SUBNETS
# =========================
resource "aws_subnet" "eks_subnet" {
  count = 2

  vpc_id     = aws_vpc.eks_vpc.id
  cidr_block = cidrsubnet(aws_vpc.eks_vpc.cidr_block, 8, count.index)

  availability_zone = element(
    ["us-east-1a", "us-east-1b"],
    count.index
  )

  map_public_ip_on_launch = true

  tags = {
    Name = "eks-subnet-${count.index}"

    # 🔥 CRITICAL FOR EKS
    "kubernetes.io/cluster/ai-agent-cluster" = "shared"
    "kubernetes.io/role/elb"                 = "1"
  }
}

# =========================
# ROUTE TABLE
# =========================
resource "aws_route_table" "rt" {
  vpc_id = aws_vpc.eks_vpc.id

  tags = {
    Name = "eks-route-table"
  }
}

# =========================
# INTERNET ROUTE
# =========================
resource "aws_route" "internet_access" {
  route_table_id         = aws_route_table.rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

# =========================
# SUBNET ASSOCIATION
# =========================
resource "aws_route_table_association" "rta" {
  count = 2

  subnet_id      = aws_subnet.eks_subnet[count.index].id
  route_table_id = aws_route_table.rt.id
}