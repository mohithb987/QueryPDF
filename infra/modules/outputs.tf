output "vpc_id" {
  value = module.networking.vpc_id
}

output "public_subnet_ids" {
  value = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "lambda_1_arn" {
  value = module.lambda.lambda_1_arn
}

output "lambda_2_arn" {
  value = module.lambda.lambda_2_arn
}

output "ecs_cluster_id" {
  value = module.ecs_cluster.ecs_cluster_id
}

output "ecs_service_arn" {
  value = module.ecs_cluster.ecs_service_arn
}