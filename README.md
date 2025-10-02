## VIMEX
### Description of the deployed app

> The provided Flask backend sets up a single route at the root URL, uses https://openweathermap.org/api, and allows us to see weather data in New York. The backend utilizes CORS to enable cross-origin requests and includes asynchronous task processing with Celery.

<img width="1634" alt="image" src="https://github.com/red512/vimex/assets/59205478/0a4b8c01-5583-453d-b74f-fd26990bd7f2">


### Prerequisites

Before getting started, make sure you have the following prerequisites set up:

1. **kubectl**: Install `kubectl`, the command-line tool for interacting with Kubernetes cluster.

2. **Helm**: Install Helm, a package manager for Kubernetes, to manage the deployment of Grafana Prometheus, ArgoCD, and Metrics server.

3. **Terraform**: Install Terraform for provisioning and managing infrastructure.
   
4. **kubeseal CLI**: Install the `kubeseal` CLI tool for encrypting Kubernetes Secrets into SealedSecret resources. You can find installation instructions [here](https://github.com/bitnami-labs/sealed-secrets#installing-kubeseal).

5. **Docker Hub Account**: Required for publishing Docker images.

6. **Slack Webhook**: Obtain a URL to send automated CI/CD notifications to Slack.

### Repository Structure

**vimex** 
https://github.com/red512/vimex

```
.
├── README.md
├── .github/workflows
│   ├── ci.yml          # CI pipeline with tests and security scanning
│   └── cd.yml          # CD pipeline with versioning and deployment
├── argocd
├── be-flask
│   ├── app.py
│   ├── requirements.txt
│   ├── test_unit.py
│   ├── test_integration.py
│   ├── version.txt
│   └── Dockerfile
└── terraform
```

**vimex-gitops**
https://github.com/red512/vimex-gitops

```
.
├── README.md
└── gitops
    └── environments
        ├── staging
        │   ├── apps
        │   └── backend-helm-chart
        └── production
            ├── apps
            └── backend-helm-chart
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



### CI/CD Pipeline

> This project implements comprehensive CI/CD pipelines using GitHub Actions for automated testing, security scanning, building, and deployment.

### CI Pipeline - Continuous Integration

<img width="538" height="824" alt="image" src="https://github.com/user-attachments/assets/2a8916a2-c77b-4990-9ba6-3414fb1687b9" />


> The CI pipeline runs on pull requests to the `main` branch and includes the following stages:

**Build Stage**
- Checks out code
- Sets up Python 3.8 environment
- Installs dependencies from `requirements.txt`

**Test Stage**
- **Unit Tests**: Runs comprehensive unit tests for application logic
- **Integration Tests**: Tests the complete application stack
  - Starts Redis server for Celery message broker
  - Launches Flask application in background
  - Starts Celery worker for async task processing
  - Verifies all services are healthy
  - Runs integration test suite
  - Automatic cleanup of all processes

**Security Stage**
- **pip-audit**: Scans Python dependencies for known vulnerabilities
- **Grype**: Performs container vulnerability scanning
- Generates security reports in GitHub Actions summary
- Fails build on medium or higher severity vulnerabilities

<img width="1057" height="624" alt="image" src="https://github.com/user-attachments/assets/cc0332ff-8f7d-4ddc-a55c-099cabb37042" />


**Notification Stage**
- Sends detailed status updates to Slack
- Includes test results, security scan status, and workflow links
- Visual indicators (✅/❌/⚠️) for quick status assessment

<img width="646" height="114" alt="image" src="https://github.com/user-attachments/assets/c2ff89d9-2cce-4f1c-9a5b-ab8fd4cb967f" />


**Trigger Events:**
- Pull requests to `main` branch (with changes in `be-flask/`)
- Manual workflow dispatch


### CD Pipeline - Continuous Deployment

<img width="443" height="1180" alt="image" src="https://github.com/user-attachments/assets/c0278b8f-e970-46ea-88b3-6a45414f5f96" />


> The CD pipeline automates the entire deployment process and includes the following stages:

**Version Bump Stage**
- Automatically increments semantic version (major.minor.patch)
- Reads current version from `be-flask/version.txt`
- Creates Git tag for the new version
- Commits version update with `[skip ci]` to prevent recursive triggers
- Validates that version tag doesn't already exist

**Build and Push Stage**
- Builds Docker images for multiple architectures (linux/amd64, linux/arm64)
- Tags images with:
  - `latest` - always points to most recent build
  - `v{version}` - semantic version tag
  - `{short-sha}` - git commit SHA for traceability
- Pushes to Docker Hub registry

**GitOps Update Stage**
- Clones the `vimex-gitops` repository
- Updates `values.yaml` in target environment (staging/production)
- Changes image tag to new version
- Commits and pushes changes to GitOps repo
- ArgoCD automatically detects and deploys the changes

**Notification Stage**
- Sends deployment status to Slack
- Includes version information, build status, and GitOps update status
- Provides direct links to workflow runs

<img width="478" height="158" alt="image" src="https://github.com/user-attachments/assets/b3e92c70-34a0-4af3-8767-fe9a5f566ceb" />


**Trigger Events:**
- Push to `main` branch (with changes in `be-flask/`)
- Manual workflow dispatch (allows choosing staging or production environment)

**Environment Strategy**
- **Staging**: Automatically deployed on every push to `main`
- **Production**: Manual deployment via workflow dispatch
- Environment-specific configurations managed in GitOps repository

### Secrets

> Sealed Secrets encrypts Kubernetes Secrets into SealedSecret resources, ensuring secure storage and transmission. These encrypted secrets can be safely stored in public repositories, with decryption occurring exclusively within the Kubernetes cluster by the Sealed Secrets controller. The encrypted secret will be stored in `sealed-secret.yaml`. You can use the next commands:

```
kubectl create secret generic api-key -n backend --from-literal=API-KEY=<api-key-example> --dry-run=client -o yaml > secret.yaml
```
```
kubeseal --controller-name selead-secrets-release-sealed-secrets --controller-namespace kube-system --format yaml < secret.yaml > sealed-secret.yaml
```

### Required GitHub Secrets

Configure these secrets in your repository settings:

**For CI/CD:**
- `API_KEY` - OpenWeatherMap API key for testing
- `SLACK_WEBHOOK_URL` - Slack webhook for notifications

**For Docker:**
- `DOCKER_HUB_USERNAME` - Docker Hub username
- `DOCKER_HUB_TOKEN` - Docker Hub access token

**For GitOps:**
- `GITOPS_DEPLOY_KEY` - SSH private key with write access to vimex-gitops repo

### Version Management

The project uses semantic versioning (MAJOR.MINOR.PATCH):

- Versions are stored in `be-flask/version.txt`
- Automatic patch version increment on every main branch commit
- Git tags created for each version (e.g., `v1.0.5`)
- Use `[skip ci]` in commit messages to skip version bump and CI

Example version progression: `1.0.0` → `1.0.1` → `1.0.2`

### Security Practices

**Automated Security Scanning**

Every CI run includes:
- **Dependency Scanning**: pip-audit checks for vulnerable Python packages
- **Container Scanning**: Grype analyzes Docker images for CVEs
- **Severity Thresholds**: Builds fail on medium or higher vulnerabilities
- **Reporting**: Detailed vulnerability reports in GitHub Actions summary

**Best Practices**
- Secrets never stored in code or configuration files
- Sealed Secrets for secure GitOps workflows
- Multi-architecture Docker builds for broader compatibility
- Regular dependency updates and security patches
- Automated alerts via Slack for security issues

### GitOps Workflow

> The project follows GitOps principles with repository separation:

1. **Application Repository (vimex)**: Contains source code, Dockerfiles, and CI/CD pipelines
2. **GitOps Repository (vimex-gitops)**: Contains Kubernetes manifests and Helm charts

**Deployment Flow**

1. Developer pushes code to `vimex` repository
2. CI pipeline runs tests and security scans
3. CD pipeline builds and pushes Docker image
4. CD pipeline updates image tag in `vimex-gitops` repository
5. ArgoCD detects changes and syncs to Kubernetes cluster
6. Application automatically deployed to target environment

**Benefits**
- **Separation of Concerns**: Code and configuration managed independently
- **Audit Trail**: All infrastructure changes tracked in Git
- **Rollback Capability**: Easy to revert to previous versions
- **Declarative**: Desired state defined in Git
- **Automated**: No manual kubectl commands needed

### Testing Infrastructure

The test suite includes:

**Unit Tests**
- Test individual functions and components
- Mock external dependencies
- Fast execution for rapid feedback

**Integration Tests**
- Full application stack testing
- Real Redis instance for Celery
- Flask app running in background
- Celery worker processing tasks
- Health check verification
- End-to-end API testing

**Test Execution**
```
# Run unit tests
cd be-flask
python test_unit.py

# Run integration tests (requires Redis)
python test_integration.py
```

### Local Development

**Running the Flask Application**
```
cd be-flask
pip install -r requirements.txt
export API_KEY=your_openweather_api_key
python app.py
```

**Running with Celery**
```
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
cd be-flask
celery -A app.celery worker --loglevel=info

# Terminal 3: Start Flask app
cd be-flask
python app.py
```

**Building Docker Image Locally**
```
cd be-flask
docker build -t flask-app:local .
docker run -p 5000:5000 -e API_KEY=your_key flask-app:local
```

### Monitoring and Observability

- Prometheus for metrics collection
- Grafana for visualization dashboards
- Horizontal Pod Autoscaler (HPA) for automatic scaling
- Health check endpoints for service monitoring

### Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass locally
4. Create a pull request to `main`
5. CI pipeline will run automatically
6. After approval and merge, CD pipeline deploys to staging
