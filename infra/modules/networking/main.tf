resource "aws_vpc" "vpc" {
  cidr_block = var.vpc_cidr
  tags = merge(
    var.common_tags,
    { "Name" = "GPI-VPC" }
  )
}

resource "aws_subnet" "public_subnets" {
  count             = length(var.public_subnet_cidr)
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = element(var.public_subnet_cidr, count.index)
  availability_zone = element(var.us_availability_zones, count.index)
  
  tags = merge(
    var.common_tags,
    { Name = "GPI-public-subnet-${count.index + 1}" }
  )
}

resource "aws_subnet" "private_subnets" {
  count             = length(var.private_subnet_cidr)
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = element(var.private_subnet_cidr, count.index)
  availability_zone = element(var.us_availability_zones, count.index)
  
  tags = merge(
    var.common_tags,
    { Name = "GPI-private-subnet-${count.index + 1}" }
  )
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = merge(
    var.common_tags,
    { Name = "GPI-IGW" }
  )
}


resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = merge(
    var.common_tags,
    { Name = "GPI-public-route" }
  )
}

resource "aws_route_table_association" "public_rt_association" {
  count          = length(aws_subnet.public_subnets)
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.vpc.id
  tags = merge(
    var.common_tags,
    { Name = "GPI-private-route" }
  )
}

resource "aws_route_table_association" "private_rt_association" {
  count          = length(aws_subnet.private_subnets)
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_route_table.id
}