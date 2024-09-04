module "ecs_sg" {
  source = "../security_group"

  vpc_id             = var.vpc_id
  security_group_name = "${var.cluster_name}-sg"
  ingress_rules = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
  egress_rules = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
  tags = var.tags
}

resource "aws_ecs_cluster" "ecs_cluster" {
  name = var.cluster_name

  tags = var.tags
}

resource "aws_ecs_task_definition" "fargate_task" {
  family                   = "${var.cluster_name}-task"
  container_definitions    = file(var.container_definition_file)
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn

  tags = var.tags
}

resource "aws_ecs_service" "ecs_service" {
  name            = "${var.cluster_name}-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.fargate_task.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [module.ecs_sg.security_group_id]
    assign_public_ip = false
  }
  tags = var.tags
}