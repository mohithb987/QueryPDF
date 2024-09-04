# VPC Configuration
vpc_cidr = "10.0.0.0/16"

# Subnet Configuration
public_subnet_cidr = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidr = ["10.0.3.0/24", "10.0.4.0/24"]

# Availability Zones
us_availability_zones = ["us-east-1a", "us-east-1c"]

# Tags
common_tags = {
  "Application" = "GPI-App"
  "Environment" = "Development"
  "Owner"       = "Mohith"
}