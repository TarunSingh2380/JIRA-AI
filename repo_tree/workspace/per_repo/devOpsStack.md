## ARCHITECTURE
This is a pure DevOps/infrastructure repository. It contains no application source code — only CI/CD pipelines, Kubernetes Helm charts, and EKS provisioning scripts.

### Top-level modules

- **.github/workflows/** — GitHub Actions CI/CD pipelines (build, deploy, cleanup, secret management)
- **eks-cdk-infra/** — Python (boto3) scripts for provisioning/destroying AWS EKS clusters; env configs in `config/`; Envoy Gateway manifests in `ramfincorp/`
- **k8s/** — Helm charts for the `ramfincorp` tenant (12 services) + common cluster resources
- **kamakshimoney-k8s/** — Helm charts for the `kamakshimoney` tenant (7 services) + common cluster resources
- **python-runner/** — Utility Docker image bundling Python, AWS CLI, kubectl, Helm, and CDK

### Two target EKS clusters
- `arn:aws:eks:ap-south-1:361795871686:cluster/ramfincorp` (prod, account 361795871686)
- `arn:aws:eks:ap-south-1:361795871686:cluster/rf-dev-eks-cluster` (dev/preprod, same account)
- KamakshiMoney cluster in account 084828595551

### External services / dependencies
- **AWS ECR** — image registry (two accounts: 361795871686, 084828595551)
- **AWS EKS** — compute target for all workloads
- **AWS IAM / OIDC** — IRSA roles for Loki, LBC, admin users
- **AWS ACM** — TLS certificates for ALB/NLB ingress
- **AWS S3** — Loki log storage (`prod-k8s-loki-chunks`, `prod-k8s-loki-ruler`)
- **HashiCorp Vault** (`https://vault.ramfincorp.com`) — secrets store, managed via `vault-secret-manager.yaml`
- **Envoy Gateway / AWS NLB** — pre-prod ingress path via `eks-cdk-infra/ramfincorp/`
- **nginx-ingress / AWS NLB** — prod ingress path

### CI/CD lifecycle
1. `build-image.yaml` (workflow_dispatch) → pulls code on self-hosted runner → builds Docker image → pushes to ECR → calls `k8s/deploy.sh <service> <tag>` via Helm
2. `deploy-prod.yaml` (workflow_dispatch) → verifies kube context → calls `k8s/deploy.sh <service> <tag>`
3. `kamakshi-build-image.yaml` / `kamakshi-deploy-prod.yaml` — mirrors for KamakshiMoney tenant using `kamakshimoney-k8s/deploy.sh`
4. `cleanup-pr-namespaces.yaml` (cron hourly) → deletes PR namespaces older than 4 hours on `rf-dev-eks-cluster`
5. `vault-secret-manager.yaml` (workflow_dispatch) → authenticates to Vault via JWT → upserts KV-v2 secrets

---

## ROUTES
This repository is infrastructure/DevOps tooling only. No HTTP routes, RPC endpoints, or message handlers are defined in this repo. Application-level routing is declared as Kubernetes Ingress rules pointing to external services.

### Kubernetes Ingress hostnames exposed per chart (nginx ingressClassName unless noted)

**k8s/ (ramfincorp)**
- `HTTPS /*  ->  rf-backend-svc:80`  (k8s/rf-backend/templates/ingress.yaml) — ALB, ramfincorp main backend
- `HTTPS /*  ->  crm-backend-svc:80`  (k8s/crm-backend/templates/ingress.yaml) — ALB, CRM backend
- `HTTPS /*  ->  loan-backend-svc:80`  (k8s/loan-backend/templates/ingress.yaml) — ALB, loan onboarding
- `HTTPS /*  ->  loans-backend-svc:80`  (k8s/loans-backend/templates/ingress.yaml) — ALB, Hyperverge loan onboarding
- `host: dedup.ramfincorp.com /  ->  dedup-svc:80`  (k8s/dedup/templates/ingress.yaml) — nginx, dedup service
- `host: dsa-backend.ramfincorp.com /(.*)  ->  dsa-backend-svc:80`  (k8s/dsa-backend/templates/ingress.yaml) — nginx, DSA backend
- `host: crm-report.ramfincorp.com /(.*)  ->  crm-report-svc:80`  (k8s/crm-report/templates/ingress.yaml) — nginx, CRM reports
- `host: notification.ramfincorp.com /(.*)  ->  notification-svc:80`  (k8s/notification/templates/ingress.yaml) — nginx, notification service
- `host: api-ramfinbackend.ramfincorp.com /(.*)  ->  rf-backend-hyperverge-svc:80`  (k8s/rf-backend-hyperverge/templates/ingress.yaml) — nginx, Hyperverge backend
- `host: userservice.ramfincorp.com /(.*)  ->  userservice-backend-svc:80`  (k8s/userservice-backend/templates/ingress.yaml) — nginx, user service
- `host: grafana.ramfincorp.com /  ->  loki-grafana:80`  (k8s/common-resources/grafana-ingress.yaml) — nginx, Grafana

**kamakshimoney-k8s/ (kamakshimoney)**
- `HTTPS /*  ->  crm-backend-svc:80`  (kamakshimoney-k8s/crm-backend/templates/ingress.yaml) — ALB, KM CRM backend
- `host: api-node.kamakshimoney.com /(.*)  ->  km-backend-svc:80`  (kamakshimoney-k8s/km-backend/templates/ingress.yaml) — nginx, KM main backend
- `host: loan-api.kamakshimoney.com /(.*)  ->  loan-backend-svc:80`  (kamakshimoney-k8s/loan-backend/templates/ingress.yaml) — nginx, KM loan API
- `host: loans-api.kamakshimoney.com /(.*)  ->  loans-backend-svc:80`  (kamakshimoney-k8s/loans-backend/templates/ingress.yaml) — nginx, KM Hyperverge loans
- `host: crm-report.kamakshimoney.com /(.*)  ->  crm-report-svc:80`  (kamakshimoney-k8s/crm-report/templates/ingress.yaml) — nginx, KM CRM reports
- `host: userservice.kamakshimoney.com /(.*)  ->  userservice-backend-svc:80`  (kamakshimoney-k8s/userservice-backend/templates/ingress.yaml) — nginx, KM user service

**eks-cdk-infra (Envoy Gateway / pre-prod)**
- `host: nginx-test.ramfincorp.com  ->  test-nginx-svc:80`  (eks-cdk-infra/ramfincorp/test-app.yaml) — Envoy Gateway HTTPRoute, test nginx
- `host: abc.preprod.ramfincorp.com  ->  your-abc-kubernetes-service-name:8080`  (eks-cdk-infra/ramfincorp/sample-route.yaml) — Envoy Gateway HTTPRoute, sample/template route

### Scheduled jobs
- `CRON 0 * * * *  ->  cleanup PR namespaces`  (.github/workflows/cleanup-pr-namespaces.yaml) — deletes k8s namespaces matching `*-pr-*` older than 4 hours

---

## DATA_MODELS
This repository contains no ORM models, database schemas, or Pydantic models. It is purely infrastructure configuration. The only structured configuration/schema objects are Helm values files and Kubernetes manifests.

### Helm Chart Configuration Schemas (in-memory / values.yaml)

**k8s/rf-backend/values.yaml**
`RfBackendValues` — fields: replicaCount, name, envSecretName, image.{repository,tag,pullPolicy}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, service.{name,type,port}, resources.{requests,limits}.{memory,cpu}, redis.resources.{requests,limits}.{cpu,memory}, ingress.certificateArn

**k8s/crm-backend/values.yaml**
`CrmBackendValues` — fields: replicaCount, name, namespace, envSecretName, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, ingress.certificateArn

**k8s/dedup/values.yaml**
`DedupValues` — fields: replicaCount, name, image.{repository,tag,pullPolicy}, namespace, service.{name,type,port}, resources.{requests,limits}.{memory,cpu}, redis.resources.{requests,limits}.{cpu,memory}

**k8s/dsa-backend/values.yaml**
`DsaBackendValues` — fields: replicaCount, name, namespace, envSecretName, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}

**k8s/loan-backend/values.yaml**
`LoanBackendValues` — fields: replicaCount, name, namespace, envSecretName, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, ingress.certificateArn

**k8s/loans-backend/values.yaml**
`LoansBackendValues` — fields: replicaCount, name, namespace, envSecretName, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, ingress.certificateArn

**k8s/razorpay-consumer/values.yaml**
`RazorpayConsumerValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, resources.{requests,limits}.{memory,cpu}

**k8s/razorpay-producer/values.yaml**
`RazorpayProducerValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, resources.{requests,limits}.{memory,cpu}

**k8s/rf-backend-hyperverge/values.yaml**
`RfBackendHypervergeValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, redis.resources.{requests,limits}.{cpu,memory}

**k8s/crm-report/values.yaml**
`CrmReportValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, redis.resources.{requests,limits}.{cpu,memory}

**k8s/notification/values.yaml**
`NotificationValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, redis.resources.{requests,limits}.{cpu,memory}

**k8s/userservice-backend/values.yaml**
`UserserviceBackendValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}

**kamakshimoney-k8s/km-backend/values.yaml**
`KmBackendValues` — fields: replicaCount, name, image.{repository,tag,pullPolicy}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, service.{name,type,port}, resources.{requests,limits}.{memory,cpu}, ingress.certificateArn

**kamakshimoney-k8s/crm-backend/values.yaml**
`KmCrmBackendValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}, ingress.{certificateArn,subnets}

**kamakshimoney-k8s/loan-backend/values.yaml**
`KmLoanBackendValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}

**kamakshimoney-k8s/loans-backend/values.yaml**
`KmLoansBackendValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}

**kamakshimoney-k8s/crm-report/values.yaml**
`KmCrmReportValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}

**kamakshimoney-k8s/userservice-backend/values.yaml**
`KmUserserviceBackendValues` — fields: replicaCount, name, namespace, image.{repository,tag,pullPolicy}, service.{name,type,port}, probe.liveness.{endpoint,initialDelaySeconds,periodSeconds}, resources.{requests,limits}.{memory,cpu}

### AWS S3 (Loki log storage)
`LokiS3Storage` (k8s/common-resources/loki/loki-values.yaml) — buckets: prod-k8s-loki-chunks (chunks), prod-k8s-loki-ruler (ruler); region: ap-south-1; retention: 28 days
