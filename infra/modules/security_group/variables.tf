variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "security_group_name" {
  description = "The name of the Security Group"
  type        = string
}

variable "ingress_rules" {
  description = "A list of ingress rules"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
}

variable "egress_rules" {
  description = "A list of egress rules"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
}

variable "tags" {
  description = "Tags to be applied to the Security Group"
  type        = map(string)
}