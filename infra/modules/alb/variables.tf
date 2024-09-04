variable "vpc_id" {
  description = "VPC ID where the ALB will be created"
  type        = string
}

variable "public_subnets" {
  description = "List of public subnet IDs where the ALB will be placed"
  type        = list(string)
}

variable "alb_name" {
  description = "Name for the ALB"
  type        = string
}

variable "tags" {
  description = "Tags to be applied to ALB resources"
  type        = map(string)
}

variable "admin_lambda_arn" {
  description = "ARN of the Lambda function for admin service"
  type        = string
}

variable "user_lambda_arn" {
  description = "ARN of the Lambda function for user service"
  type        = string
}