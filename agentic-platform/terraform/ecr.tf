resource "aws_ecr_repository" "ai_agent_repo" {
  name = "ai-agent"

  image_scanning_configuration {
    scan_on_push = true
  }

  image_tag_mutability = "MUTABLE"

  tags = {
    Project = "ai-agent-platform"
  }
}

output "ecr_repository_url" {
  value = aws_ecr_repository.ai_agent_repo.repository_url
}