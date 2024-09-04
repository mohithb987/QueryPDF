variable "vpc_id" {
  description = "VPC ID where the ECS cluster will be created"
  type        = string
}

variable "private_subnets" {
  description = "List of private subnet IDs where the ECS tasks will be placed"
  type        = list(string)
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "cpu" {
  description = "The number of cpu units used by the task"
  type        = string
  default     = "256"
}

variable "memory" {
  description = "The amount of memory (in MiB) used by the task"
  type        = string
  default     = "512"
}

variable "execution_role_arn" {
  description = "ARN of the IAM role that allows ECS to pull container images"
  type        = string
}

variable "container_definition_file" {
  description = "Path to the JSON file containing the container definitions"
  type        = string
}

variable "desired_count" {
  description = "The number of instantiations of the task"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags to be applied to ECS resources"
  type        = map(string)
}