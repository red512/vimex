## VIMEX
### Description of the deployed app

> The provided Flask backend sets up a single route at the root URL, uses https://openweathermap.org/api, and allows us to see weather data in New York. The backend utilizes CORS to enable cross-origin requests.

<img width="1634" alt="image" src="https://github.com/red512/vimex/assets/59205478/0a4b8c01-5583-453d-b74f-fd26990bd7f2">


### Prerequisites

Before getting started, make sure you have the following prerequisites set up:

1. **kubectl**: Install `kubectl`, the command-line tool for interacting with Kubernetes cluster.

2. **Helm**: Install Helm, a package manager for Kubernetes, to manage the deployment of Grafana Prometheus, ArgoCD, and Metrics server.

3. **Terraform**: Install Terraform for provisioning and managing infrastructure.
   
4. **kubeseal CLI**: Install the `kubeseal` CLI tool for encrypting Kubernetes Secrets into SealedSecret resources. You can find installation instructions [here](https://github.com/bitnami-labs/sealed-secrets#installing-kubeseal).

6. **Slack Webhook**: Obtain a URL to send automated CI notifications to Slack.

### Repository Structure

**vimex** 
https://github.com/red512/vimex

```
.
├── README.md
├── argocd
├── be-flask
└── terraform

```

**vimex-gitops**
https://github.com/red512/vimex-gitops

```
.
├── README.md
└── environments
    └── staging
        ├── apps
        └── backend
```

### k8s cluster

> Here I used EKS cluster that was created in Terraform but you can use any cloud provider or work with minikube.
> In this example I used AWS and also left commented out the part for minikube usage.

```
# provider "helm" {
#   kubernetes {
#     config_path = "~/.kube/config"
#   }
# }
```

<img width="1110" alt="image" src="https://github.com/red512/vimex/assets/59205478/75a51295-3229-4691-83b8-db2f061cfac2">

### Application Helm chart overview

```
.
├── Chart.yaml
├── templates
│   ├── deployment.yaml
│   ├── hpa.yaml
│   ├── namespace.yaml
│   ├── sealed-secret.yaml
│   └── service.yaml
└── values.yaml
```

### Deployments

> The deployments done with ArgoCD.
- APPS-STAGING
![image](https://github.com/red512/vimex/assets/59205478/d182fc5a-0b4a-4869-842d-44538620348d)
>
- BACKEND APP
![image](https://github.com/red512/vimex/assets/59205478/0655ce87-bc71-4922-842f-5688685588a1)



### Github actions

> Github action was used to build CI including tests, build, and publish steps

### Secrets

> Sealed Secrets encrypts Kubernetes Secrets into SealedSecret resources, ensuring secure storage and transmission. These encrypted secrets can be safely stored in public repositories, with decryption occurring exclusively within the Kubernetes cluster by the Sealed Secrets controller. The encrypted secret will be stored in `sealed-secret.yaml`. You can use the next commands:

```
kubectl create secret generic api-key -n backend --from-literal=API-KEY=<api-key-example> --dry-run=client -o yaml > secret.yaml
```
```
kubeseal --controller-name selead-secrets-release-sealed-secrets --controller-namespace kube-system --format yaml < secret.yaml > sealed-secret.yaml
```

### CI Details

### CI Tests Workflows

This GitHub Action automates testing for backend and responds to various events:

- `Push`: Triggers when changes are pushed to the 'main' branch within the respective directories ('be-flask/' for backend).
- `Workflow Dispatch`: Allows manual triggering of the workflow.
- `Pull Request`: Triggers on pull requests to the respective branches.
  The workflow includes steps for setting up the environment, installing dependencies, running tests, and notifying the team of success or failure via Slack messages.

For Slack notifications, set up the Slack webhook URL as a secret in your repository.

![image](https://github.com/red512/vimex/assets/59205478/8b30bd4f-bd1a-4413-bcdb-dc782c1b0cea)


### Publish Workflows

These GitHub Actions manage the image publication for backend components in the project. Depending on the context, the workflows respond to various events:

- `Push`: Triggers when changes are pushed to the 'main' branch within the respective directories ('be-flask/' for backend).
- `Workflow Dispatch`: Allows manual triggering of the workflow.
- `Tags`: Triggers on tag creation with a version pattern ('v\*').
  The workflow includes steps for checking out the code, generating Docker metadata, logging in to DockerHub, building Docker images, and pushing them to the repository.

For Docker image publishing, ensure you have DockerHub credentials set up as secrets in your repository.
For Slack notifications, set up the Slack webhook URL as a secret in your repository.
