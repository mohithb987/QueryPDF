variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnets"
  type        = list(string)
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnets"
  type        = list(string)
}

variable "us_availability_zones" {
  description = "Availability Zones"
  type        = list(string)
}

variable "lambda_zip_file_path" {
  description = "Path to the Lambda function's zip file"
  type        = string
}

variable "admin_lambda_arn" {
  description = "ARN of the Lambda function for admin service"
  type        = string
}

variable "user_lambda_arn" {
  description = "ARN of the Lambda function for user service"
  type        = string
}

variable "container_definition_file_path" {
  description = "Path to the ECS container definition file"
  type        = string
}

variable "ecs_cpu" {
  description = "CPU units for ECS task"
  type        = string
}

variable "ecs_memory" {
  description = "Memory for ECS task"
  type        = string
}

variable "common_tags" {
  description = "A map of tags to assign to resources"
  type        = map(string)
}