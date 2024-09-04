variable "tags" {
  type = map(string)
  default = {
    "Application" = "GPI-App"
    "Environment" = "Development"
    "Owner"       = "Mohith"
  }
}

output "common_tags" {
  value = var.tags
}