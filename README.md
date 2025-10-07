## VIMEX
### Description of the deployed app

> A cloud-native Flask application demonstrating Kubernetes deployment with **KEDA autoscaling**, **Argo Rollouts**, and **GitOps**. The backend provides weather data via OpenWeatherMap API with  **Redis-based queue processing** that automatically scales Celery worker pods based on demand. Features include **zero-downtime deployments**, **event-driven autoscaling**, and comprehensive **CI/CD automation**.

<img width="1634" alt="image" src="https://github.com/red512/vimex/assets/59205478/0a4b8c01-5583-453d-b74f-fd26990bd7f2">


### Prerequisites

Before getting started, make sure you have the following prerequisites set up:

1. **kubectl**: Install `kubectl`, the command-line tool for interacting with Kubernetes cluster.

2. **Helm**: Install Helm, a package manager for Kubernetes, to manage the deployment of Grafana, Prometheus, ArgoCD, KEDA, and Metrics server.

3. **Terraform**: Install Terraform for provisioning and managing infrastructure.
   
4. **kubeseal CLI**: Install the `kubeseal` CLI tool for encrypting Kubernetes Secrets into SealedSecret resources. You can find installation instructions [here](https://github.com/bitnami-labs/sealed-secrets#installing-kubeseal).

5. **KEDA**: Kubernetes Event-driven Autoscaler for Redis queue-based scaling. 

6. **Argo Rollouts**: with canary deployment.

7. **Docker Hub Account**: Required for publishing Docker images.

8. **Slack Webhook**: Obtain a URL to send automated CI/CD notifications to Slack.

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
├── test_keda_scaling.py         # KEDA autoscaling test script
└── gitops
    └── environments
        ├── staging
        │   ├── apps
        │   │   └── backend.yaml # ArgoCD Application
        │   └── backend-helm-chart
        │       ├── Chart.yaml
        │       ├── values.yaml
        │       └── templates
        │           ├── rollout.yaml          # API pods (Argo Rollout)
        │           ├── rollout-worker.yaml   # Worker pods (Argo Rollout)
        │           ├── scaling/
        │           │   └── scaled-object.yaml # KEDA ScaledObject
        │           ├── service.yaml
        │           ├── namespace.yaml
        │           └── sealed-secret.yaml
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

### Application Helm Chart Overview

```
backend-helm-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── namespace.yaml           # Backend namespace
│   ├── sealed-secret.yaml       # Encrypted API keys
│   ├── service.yaml            # Backend API service
│   ├── rollout.yaml            # Argo Rollout for API pods
│   ├── rollout-worker.yaml     # Argo Rollout for Celery workers
│   └── scaling/
│       └── scaled-object.yaml  # KEDA ScaledObject for Redis-based autoscaling
```

**Key Components:**

- **Rollouts**: Advanced deployment strategies for both API and worker pods
- **KEDA Scaling**: Redis queue-based autoscaling for Celery workers  
- **Sealed Secrets**: Secure API key management with GitOps

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

#### Docker Compose (Recommended)

The easiest way to run the application locally is using Docker Compose, which sets up the entire stack including Flask app, Redis, and Celery worker.

**Prerequisites**
- Docker and Docker Compose installed
- OpenWeatherMap API key (get one [here](https://openweathermap.org/api))

**Quick Start**
```bash
# 1. Set up environment variables
make setup
# Edit .env file and add your API key

# 2. Start the application
make build

# 3. Access the application
# Flask app: http://localhost:5000
```

**Available Make Commands**
```bash
make help   # Show all available commands
make setup  # Copy .env.example to .env
make up     # Start all services
make build  # Build and start all services
make down   # Stop all services
make logs   # Show logs from all services
make test   # Run tests in containers
make clean  # Remove all containers and volumes
```

**Manual Docker Compose Commands**
```bash
# Start all services
docker compose up

# Build and start
docker compose up --build

# Stop services
docker compose down

# View logs
docker compose logs -f
```

**Services Included**
- **flask-app**: Main Flask application (port 5000)
- **redis**: Redis server for Celery broker/backend (port 6379)
- **celery-worker**: Celery worker for async task processing

#### Manual Setup (Alternative)

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

### KEDA Autoscaling & Redis Queue Management

The application implements advanced autoscaling using KEDA (Kubernetes Event-driven Autoscaling) that scales Celery worker pods based on Redis queue length.

#### Architecture Overview

**Component Architecture:**
- **Backend API Pod**: Flask application serving weather API requests
- **Worker Pods**: Celery workers processing async tasks via Argo Rollouts
- **Redis**: Message broker and result backend for Celery tasks
- **KEDA ScaledObject**: Monitors Redis queue and triggers scaling events
- **Horizontal Pod Autoscaler (HPA)**: Created by KEDA to manage worker replica scaling

**Scaling Logic:**
- **Trigger**: Redis queue length > 5 tasks
- **Scale Down**: Back to 1 pod when queue length < 5
- **Polling**: Every 10 seconds for responsive scaling
- **Cooldown**: 30 seconds before scaling down to prevent thrashing


#### Testing KEDA Scaling

The project includes a comprehensive test script for validating KEDA scaling behavior:

**Quick Start:**
```bash
# Navigate to GitOps repository
cd vimex-gitops

# Test scaling with 50 real city weather tasks
python test_keda_scaling.py --add-tasks 50 --duration 5

# Monitor scaling behavior in real-time
python test_keda_scaling.py --monitor-only --duration 10

# Clear queue before testing
python test_keda_scaling.py --clear-queue
```

**Test Script Features:**
- ✅ **Real City Data**: Uses actual cities (London, Tokyo, NYC) for realistic API calls
- ✅ **Complete Message Format**: Properly formatted Celery/Kombu messages
- ✅ **Redis Integration**: Connects via kubectl exec to backend pods
- ✅ **Scaling Monitoring**: Real-time pod count and queue length tracking
- ✅ **Load Testing**: Supports 1000+ tasks for sustained scaling tests

**Example Output:**
```
🚀 KEDA Redis Queue Scaling Test
==================================================
✅ Redis connection verified

📊 Initial State:
   Queue Length: 0
   Pod Count: 1
   KEDA Ready: True

📝 Adding 50 tasks to trigger scaling...
✅ Queue length (47) exceeds threshold (5)
   🎯 KEDA should scale up to 2-3 replicas

Time         Queue    Pods   KEDA Ready   Action
--------------------------------------------------------------------------------
18:18:38     44       1      True         Should scale UP
18:18:53     35       2      True         Scaling correctly
18:19:08     12       3      True         Scaled correctly
18:19:23     0        1      True         Scaled down
```

**Advanced Testing:**
```bash
# Sustained load testing with 1000 tasks
python test_keda_scaling.py --add-tasks 1000 --duration 10

# Continuous load to maintain scaling
while true; do 
  python test_keda_scaling.py --add-tasks 100
  sleep 30
done

# Monitor with real-time updates
watch -n 2 'kubectl get pods -n backend -l app=worker'
```

#### Argo Rollouts Integration

Workers are deployed using Argo Rollouts for advanced deployment strategies:

**Rollout Configuration:**
- **Canary Strategy**: 100% traffic weight for immediate deployment
- **Health Probes**: `celery inspect ping` for accurate health checking
- **Solo Pool**: Bypasses Celery QoS issues with Redis compatibility
- **Resource Limits**: Optimized for efficient task processing

**Worker Configuration:**
```yaml
# Celery worker optimized for Redis scaling
command: ["celery"]
args:
  - "-A"
  - "app.celery"
  - "worker"
  - "--concurrency=1"
  - "--pool=solo"          # Critical for Redis compatibility
  - "--without-gossip"     # Reduces overhead
  - "--without-mingle"     # Improves startup time
```



### Monitoring and Observability

- **KEDA Metrics**: Queue length, scaling events, and HPA status
- **Prometheus**: Application metrics and scaling behavior
- **Grafana**: Real-time dashboards for queue depth and pod scaling
- **Argo Rollouts**: Deployment health and rollback capabilities
- **Health Checks**: Celery worker health via `inspect ping` command

### Quick Reference - KEDA Operations

**Testing Autoscaling:**
```bash
# Basic scaling test with 50 tasks
python test_keda_scaling.py --add-tasks 50

# Monitor scaling behavior
python test_keda_scaling.py --monitor-only --duration 10

# Load test with 1000 tasks
python test_keda_scaling.py --add-tasks 1000 --duration 15

# Clear queue
python test_keda_scaling.py --clear-queue
```

### Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Test KEDA scaling if modifying worker configuration
4. Ensure all tests pass locally
5. Create a pull request to `main`
6. CI pipeline will run automatically
7. After approval and merge, CD pipeline deploys to staging
