module "iam" {
  source    = "./modules/iam"
  tags      = var.common_tags
}

module "networking" {
  source = "./modules/networking"

  vpc_cidr            = var.vpc_cidr
  public_subnet_cidr  = var.public_subnet_cidr
  private_subnet_cidr = var.private_subnet_cidr
  us_availability_zones = var.us_availability_zones

  common_tags = var.common_tags
}

module "alb" {
  source = "./modules/alb"

  vpc_id         = module.networking.vpc_id
  public_subnets = module.networking.public_subnet_ids

  alb_name = "gpi-alb"
  tags     = var.common_tags
  admin_lambda_arn = var.admin_lambda_arn
  user_lambda_arn  = var.user_lambda_arn
}

module "lambda" {
  source = "./modules/lambda"

  vpc_id          = module.networking.vpc_id
  public_subnets  = module.networking.public_subnet_ids

  lambda_name_1    = "lambda-function-1"
  lambda_name_2    = "lambda-function-2"
  lambda_zip_file  = var.lambda_zip_file_path
  tags             = var.common_tags
}

module "ecs" {
  source = "./modules/ecs"

  vpc_id          = module.networking.vpc_id
  private_subnets = module.networking.private_subnet_ids

  cluster_name              = "ecs-cluster"
  container_definition_file = var.container_definition_file_path
  cpu                       = var.ecs_cpu
  memory                    = var.ecs_memory
  desired_count             = 1
  execution_role_arn        = aws_iam_role.ecs_task_exec_role.arn
  tags                      = var.common_tags
}