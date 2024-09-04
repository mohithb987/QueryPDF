variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR blocks for the public subnets"
  type        = list(string)
}

variable "private_subnet_cidr" {
  description = "CIDR blocks for the private subnets"
  type        = list(string)
}

variable "us_availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "common_tags" {
  description = "Common tags to be applied to resources"
  type        = map(string)
}