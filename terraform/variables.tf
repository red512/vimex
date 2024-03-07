# ------------------------------------------------------------
# EKS Cluster Settings
# ------------------------------------------------------------
variable "cluster_name" {
  type        = string
  description = "The name of the EKS cluster."
  default     = "my-eks"
}

variable "cluster_version" {
  type        = string
  description = "The version of the EKS cluster."
  default     = "1.23"
}

variable "worker_group_instance_type" {
  type        = list(string)
  description = "The instance type of the worker group nodes. Must be large enough to support the amount of NICS assigned to pods."
  default     = ["t3.small"]
}

variable "autoscaling_group_min_size" {
  type        = number
  description = "The minimum number of nodes the worker group can scale to."
  default     = 1
}

variable "autoscaling_group_desired_capacity" {
  type        = number
  description = "The desired number of nodes the worker group should attempt to maintain."
  default     = 2
}

variable "autoscaling_group_max_size" {
  type        = number
  description = "The maximum number of nodes the worker group can scale to."
  default     = 3
}

# ------------------------------------------------------------
# Networking Settings
# ------------------------------------------------------------

variable "private_subnets" {
  description = "List of private subnets CIDR blocks."
  type        = list(string)
  default     = ["10.0.0.0/22", "10.0.32.0/22"]
}

variable "public_subnets" {
  description = "List of public subnets CIDR blocks."
  type        = list(string)
  default     = ["10.0.64.0/22", "10.0.96.0/22"]
}

variable "azs" {
  description = "Availability Zones to distribute resources."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1c"]
}

