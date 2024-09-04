variable "vpc_id" {
  description = "VPC ID where the Lambda functions will be deployed"
  type        = string
}

variable "public_subnets" {
  description = "List of public subnet IDs where the Lambda functions will be placed"
  type        = list(string)
}

variable "lambda_name_1" {
  description = "Name of the first Lambda function"
  type        = string
}

variable "lambda_name_2" {
  description = "Name of the second Lambda function"
  type        = string
}

variable "lambda_zip_file" {
  description = "Path to the zip file containing the Lambda function code"
  type        = string
}

variable "tags" {
  description = "Tags to be applied to Lambda resources"
  type        = map(string)
}