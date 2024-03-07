resource "helm_release" "prometheus" {
  name             = "prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "48.1.1"
  namespace        = "monitoring"
  create_namespace = true
  values = [
    file("helm-values/prometheus-values.yaml")
  ]
}

