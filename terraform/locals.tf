# ------------------------------------------------------------
# AIM Policy Settings
# ------------------------------------------------------------
locals {
  eks_access_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["eks:DescribeCluster"],
        Effect   = "Allow",
        Resource = "*",
      },
    ]
  }

  allow_assume_eks_admins_policy_json = {
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["sts:AssumeRole"]
        Effect   = "Allow"
        Resource = module.eks_admins_iam_role.iam_role_arn
      },
    ]
  }

  encoded_eks_access_policy              = jsonencode(local.eks_access_policy)
  encoded_allow_assume_eks_admins_policy = jsonencode(local.allow_assume_eks_admins_policy_json)

}

