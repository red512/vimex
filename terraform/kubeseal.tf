resource "helm_release" "kubeseal" {
  name       = "kubeseal"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kubeseal"
  version    = "0.16.0" # Or specify the version you need

  set {
    name  = "controller.replicaCount"
    value = "1"
  }

  set {
    name  = "secretsProviders[0]"
    value = "kubernetes"
  }
}
