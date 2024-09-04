module "lambda_sg" {
  source = "../security_group"

  vpc_id             = var.vpc_id
  security_group_name = "${var.lambda_name_1}-sg"
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

resource "aws_lambda_function" "lambda_1" {
  function_name = var.lambda_name_1
  role          = module.iam.lambda_role_arn
  handler       = "index.handler"
  runtime       = "python3.8"
  filename      = var.lambda_zip_file
  vpc_config {
    subnet_ids         = [element(var.public_subnets, 0)]
    security_group_ids = [module.lambda_sg.security_group_id]
  }
  tags = var.tags
}

resource "aws_lambda_function" "lambda_2" {
  function_name = var.lambda_name_2
  role          = module.iam.lambda_role_arn
  handler       = "index.handler"
  runtime       = "python3.8"
  filename      = var.lambda_zip_file
  vpc_config {
    subnet_ids         = [element(var.public_subnets, 1)]
    security_group_ids = [module.lambda_sg.security_group_id]
  }
  tags = var.tags
}