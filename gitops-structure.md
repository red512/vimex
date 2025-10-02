# GitOps Repository Structure for Argo Rollouts

This document describes how the Argo Rollouts configuration should be organized in the separate `vimex-gitops` repository.

## Repository Structure

The GitOps repository should have the following simplified structure:

```
vimex-gitops/
├── README.md
├── argocd/
│   └── applications/
│       ├── backend-staging.yaml
│       ├── backend-production.yaml
│       ├── redis-staging.yaml
│       ├── redis-production.yaml
│       └── monitoring.yaml
└── k8s/
    ├── backend-helm-chart/
    │   ├── Chart.yaml
    │   ├── values-staging.yaml
    │   ├── values-production.yaml
    │   └── templates/
    │       ├── _helpers.tpl
    │       ├── namespace.yaml
    │       ├── rollout.yaml
    │       ├── service.yaml
    │       ├── ingress.yaml
    │       ├── analysistemplate.yaml
    │       └── configmap.yaml
    ├── redis-helm-chart/
    │   ├── Chart.yaml
    │   ├── values-staging.yaml
    │   ├── values-production.yaml
    │   └── templates/
    │       ├── _helpers.tpl
    │       ├── namespace.yaml
    │       ├── deployment.yaml
    │       ├── service.yaml
    │       └── configmap.yaml
    └── monitoring/
        ├── loki-stack.yaml
        ├── prometheus-rules.yaml
        └── grafana-dashboard.yaml
```

## Backend Helm Chart Configuration

### k8s/backend-helm-chart/Chart.yaml
```yaml
apiVersion: v2
name: vimex-backend
description: A Helm chart for Vimex Backend with Argo Rollouts support
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - flask
  - backend
  - weather
  - canary
  - rollouts
home: https://github.com/red512/vimex
sources:
  - https://github.com/red512/vimex
maintainers:
  - name: Vimex Team
    email: team@vimex.io
```

### k8s/backend-helm-chart/values-staging.yaml
```yaml
# Staging environment configuration
environment: staging

image:
  repository: projectred521/flask-w
  tag: v1.0.6
  pullPolicy: IfNotPresent

namespace:
  name: backend-staging
  create: true

rollout:
  enabled: true
  strategy: canary
  replicas: 3
  canary:
    steps:
      - setWeight: 20
      - pause: {duration: 30s}
      - analysis:
          templates:
            - templateName: success-rate
          args:
            - name: service-name
              value: vimex-backend-canary
      - setWeight: 50
      - pause: {duration: 30s}
      - setWeight: 80
      - pause: {duration: 30s}

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api-staging.vimex.local
      paths:
        - path: /
          pathType: Prefix

env:
  FLASK_ENV: production
  FLASK_DEBUG: "0"
  CELERY_BROKER_URL: redis://redis.backend-staging.svc.cluster.local:6379/0
  CELERY_RESULT_BACKEND: redis://redis.backend-staging.svc.cluster.local:6379/0
  LOG_LEVEL: INFO

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### k8s/backend-helm-chart/values-production.yaml
```yaml
# Production environment configuration
environment: production

image:
  repository: projectred521/flask-w
  tag: v1.0.6
  pullPolicy: IfNotPresent

namespace:
  name: backend-production
  create: true

rollout:
  enabled: true
  strategy: canary
  replicas: 5
  canary:
    steps:
      - setWeight: 10
      - pause: {duration: 60s}
      - analysis:
          templates:
            - templateName: success-rate
          args:
            - name: service-name
              value: vimex-backend-canary
      - setWeight: 25
      - pause: {} # Manual approval for production
      - setWeight: 50
      - pause: {duration: 120s}
      - setWeight: 75
      - pause: {duration: 120s}

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.vimex.io
      paths:
        - path: /
          pathType: Prefix

env:
  FLASK_ENV: production
  FLASK_DEBUG: "0"
  CELERY_BROKER_URL: redis://redis.backend-production.svc.cluster.local:6379/0
  CELERY_RESULT_BACKEND: redis://redis.backend-production.svc.cluster.local:6379/0
  LOG_LEVEL: WARNING

resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## Redis Helm Chart Configuration

### k8s/redis-helm-chart/Chart.yaml
```yaml
apiVersion: v2
name: vimex-redis
description: Redis for Vimex Backend Celery broker and result backend
type: application
version: 0.1.0
appVersion: "7.4.5"
keywords:
  - redis
  - cache
  - celery
  - broker
```

### k8s/redis-helm-chart/values-staging.yaml
```yaml
# Staging Redis configuration
environment: staging

namespace:
  name: backend-staging
  create: false # Backend chart creates it

image:
  repository: redis
  tag: "7-alpine"
  pullPolicy: IfNotPresent

redis:
  persistence:
    enabled: false # No persistence for staging
  resources:
    requests:
      memory: "64Mi"
      cpu: "50m"
    limits:
      memory: "128Mi"
      cpu: "100m"
  config:
    maxmemory: "64mb"
    maxmemory-policy: "allkeys-lru"
    save: ""
    appendonly: "no"
```

### k8s/redis-helm-chart/values-production.yaml
```yaml
# Production Redis configuration
environment: production

namespace:
  name: backend-production
  create: false # Backend chart creates it

image:
  repository: redis
  tag: "7-alpine"
  pullPolicy: IfNotPresent

redis:
  persistence:
    enabled: true
    size: 8Gi
    storageClass: "gp2"
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "200m"
  config:
    maxmemory: "256mb"
    maxmemory-policy: "allkeys-lru"
    save: "900 1"
    appendonly: "yes"
```

### k8s/redis-helm-chart/templates/deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "vimex-redis.fullname" . }}
  namespace: {{ .Values.namespace.name }}
  labels:
    {{- include "vimex-redis.labels" . | nindent 4 }}
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "vimex-redis.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "vimex-redis.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: redis
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: 6379
          name: redis
        command:
        - redis-server
        - /etc/redis/redis.conf
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        {{- if .Values.redis.persistence.enabled }}
        - name: redis-data
          mountPath: /data
        {{- end }}
        resources:
          {{- toYaml .Values.redis.resources | nindent 10 }}
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-config
        configMap:
          name: {{ include "vimex-redis.fullname" . }}-config
      {{- if .Values.redis.persistence.enabled }}
      - name: redis-data
        persistentVolumeClaim:
          claimName: {{ include "vimex-redis.fullname" . }}-data
      {{- end }}
```

## ArgoCD Application Configuration

### argocd/applications/backend-staging.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vimex-backend-staging
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "2"
spec:
  project: default
  source:
    repoURL: https://github.com/red512/vimex-gitops
    targetRevision: HEAD
    path: k8s/backend-helm-chart
    helm:
      valueFiles:
      - values-staging.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: backend-staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    - ServerSideApply=true
```

### argocd/applications/backend-production.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vimex-backend-production
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "2"
spec:
  project: default
  source:
    repoURL: https://github.com/red512/vimex-gitops
    targetRevision: HEAD
    path: k8s/backend-helm-chart
    helm:
      valueFiles:
      - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: backend-production
  syncPolicy:
    syncOptions:
    - CreateNamespace=true
    - ServerSideApply=true
    # No automated sync for production - manual approval required
```

### argocd/applications/redis-staging.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vimex-redis-staging
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "1"
spec:
  project: default
  source:
    repoURL: https://github.com/red512/vimex-gitops
    targetRevision: HEAD
    path: k8s/redis-helm-chart
    helm:
      valueFiles:
      - values-staging.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: backend-staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - ServerSideApply=true
```

### argocd/applications/redis-production.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vimex-redis-production
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "1"
spec:
  project: default
  source:
    repoURL: https://github.com/red512/vimex-gitops
    targetRevision: HEAD
    path: k8s/redis-helm-chart
    helm:
      valueFiles:
      - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: backend-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - ServerSideApply=true
```

### argocd/applications/monitoring.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vimex-monitoring
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "0"
spec:
  project: default
  source:
    repoURL: https://github.com/red512/vimex-gitops
    targetRevision: HEAD
    path: k8s/monitoring
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

## Updated CI/CD Pipeline Integration

The CD pipeline in the main `vimex` repository should update the simplified GitOps structure:

```bash
# In the CD pipeline (update-gitops step)
git clone git@github.com:red512/vimex-gitops.git
cd vimex-gitops

# Update staging automatically
if [ "${{ github.event_name }}" == "push" ]; then
  ENVIRONMENT="staging"
  VALUES_FILE="k8s/backend-helm-chart/values-staging.yaml"
elif [ "${{ github.event.inputs.environment }}" == "production" ]; then
  ENVIRONMENT="production"
  VALUES_FILE="k8s/backend-helm-chart/values-production.yaml"
else
  ENVIRONMENT="staging"
  VALUES_FILE="k8s/backend-helm-chart/values-staging.yaml"
fi

# Update image tag in the appropriate values file
sed -i "s/tag: v[0-9]\+\.[0-9]\+\.[0-9]\+/tag: v$NEW_VERSION/" "$VALUES_FILE"
sed -i "s/tag: manual-.*/tag: v$NEW_VERSION/" "$VALUES_FILE"

git add "$VALUES_FILE"
git commit -m "chore: update backend image to v$NEW_VERSION for $ENVIRONMENT"
git push origin main
```

## Auto-Sync Configuration

With this structure, ArgoCD will automatically sync from the `k8s/` directory:

1. **Monitoring** deploys first (sync-wave: 0)
2. **Redis** deploys second (sync-wave: 1)
3. **Backend** deploys last (sync-wave: 2)

**Auto-sync enabled for:**
- Staging environment (both Redis and Backend)
- Monitoring stack

**Manual sync required for:**
- Production environment (safety gate)

## Log Monitoring Commands

```bash
# Watch rollout progress
kubectl argo rollouts get rollout vimex-backend -n backend-staging --watch

# Monitor logs by environment
kubectl logs -l app=vimex-backend -n backend-staging -f --prefix=true
kubectl logs -l app=vimex-backend -n backend-production -f --prefix=true

# Query canary logs via Loki
curl -s "http://loki.monitoring.svc.cluster.local:3100/loki/api/v1/query_range" \
  -G --data-urlencode 'query={app="vimex-backend",namespace="backend-staging",rollout_revision!=""}' \
  --data-urlencode 'start=30m'
```

This simplified structure provides:
- ✅ **Cleaner GitOps organization** with `k8s/` instead of nested `environments/`
- ✅ **Separate Redis Helm chart** for better dependency management
- ✅ **Auto-sync with proper sync waves** for deployment ordering
- ✅ **Environment-specific configurations** via separate values files
- ✅ **Production safety** with manual sync approval
- ✅ **Simplified CI/CD integration** with single directory structure