# helm install argocd -n argocd --create-namespace argo/argo-cd --version 3.35.4 -f terraform/values/argocd.yaml

resource "helm_release" "argocd" {
  name = "argocd"

  repository       = "argo"
  chart            = "argo-cd"
  namespace        = "argo"
  create_namespace = true
  version          = "3.35.4"

  values = [file("helm-values/argocd-values.yaml")]
}
