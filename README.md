### vimex
### Description of the deployed app

> The provided Flask backend sets up a single route at the root URL, uses https://openweathermap.org/api, and allows us to see weather data in New York. The backend utilizes CORS to enable cross-origin requests.

<img width="1638" alt="image" src="https://github.com/red512/vimex/assets/59205478/74f22c7d-b20f-423b-8a58-1779cf277485">

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
> In this example I used AWS and also left commented out part for minikube usage.

<img width="1110" alt="image" src="https://github.com/red512/vimex/assets/59205478/75a51295-3229-4691-83b8-db2f061cfac2">


### Deployments

> The deployments done with ArgoCD.

### Github actions

> Github action was used to build CI including tests, build, and publish steps

### Secrets

> Sealed Secrets encrypts Kubernetes Secrets into SealedSecret resources, ensuring secure storage and transmission. These encrypted secrets can be safely stored in public repositories, with decryption occurring exclusively within the Kubernetes cluster by the Sealed Secrets controller. You can use next commands:

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

### Publish Workflows

These GitHub Actions manage the image publication for backend components in the project. Depending on the context, the workflows respond to various events:

- `Push`: Triggers when changes are pushed to the 'main' branch within the respective directories ('be-flask/' for backend).
- `Workflow Dispatch`: Allows manual triggering of the workflow.
- `Tags`: Triggers on tag creation with a version pattern ('v\*').
  The workflow includes steps for checking out the code, generating Docker metadata, logging in to DockerHub, building Docker images, and pushing them to the repository.

For Docker image publishing, ensure you have DockerHub credentials set up as secrets in your repository.
For Slack notifications, set up the Slack webhook URL as a secret in your repository.
