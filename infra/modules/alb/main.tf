module "alb_sg" {
  source = "../security_group"

  vpc_id             = var.vpc_id
  security_group_name = "${var.alb_name}-sg"
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

resource "aws_lb" "alb" {
  name            = var.alb_name
  internal        = false
  load_balancer_type = "application"
  security_groups = [module.alb_sg.security_group_id]
  subnets         = var.public_subnets

  tags = var.tags
}

resource "aws_lb_target_group" "tg" {
  name        = "${var.alb_name}-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  tags = var.tags
}

resource "aws_lb_listener" "listener" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }

  tags = var.tags
}

resource "aws_lb_listener_rule" "admin_rule" {
  listener_arn = aws_lb_listener.listener.arn
  priority     = 1

  condition {
    path_pattern {
      values = ["/admin*"]
    }
  }

  action {
    type        = "lambda"
    target_group_arn  = var.admin_lambda_arn
  }

  tags = var.tags
}

resource "aws_lb_listener_rule" "user_rule" {
  listener_arn = aws_lb_listener.listener.arn
  priority     = 2

  condition {
    path_pattern {
      values = ["/user*"]
    }
  }

  action {
    type        = "lambda"
    target_group_arn  = var.user_lambda_arn
  }

  tags = var.tags
}
