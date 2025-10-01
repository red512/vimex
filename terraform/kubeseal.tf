resource "helm_release" "sealed_secrets" {
  name             = "selead-secrets-release"
  repository       = "sealed-secrets"
  chart            = "sealed-secrets"
  # version          = "48.1.1"
  namespace        = "kube-system"
}


