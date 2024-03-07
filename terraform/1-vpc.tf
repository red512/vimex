module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "main"
  cidr = "10.0.0.0/20"

  azs             = var.azs
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  enable_nat_gateway     = true
  enable_vpn_gateway     = true
  one_nat_gateway_per_az = false

  enable_dns_hostnames = true
  single_nat_gateway   = true

  tags = {
    Environment = "dev"
  }
}



