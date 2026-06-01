# Architecture Map

## DSA-Backend

```
DSA-Backend (Express/TypeScript Node.js service)
├── Entry Points
│   ├── src/server.ts          — HTTP server (registers all routes, boots App)
│   └── src/consumer.ts        — SQS consumer (separate process, polls queue)
│
├── src/app.ts                 — Express App class: middleware, routes, DB init, cron, swagger
│
├── Top-level Modules
│   ├── routes/                — Route definitions (auth, dsa, media, user, index)
│   ├── controllers/           — Request handlers (auth, dsa, media, users, index)
│   ├── services/              — Business logic
│   │   ├── auth.service.ts
│   │   ├── users.service.ts
│   │   ├── dsa.service.ts
│   │   ├── s3MediaUpload.service.ts
│   │   ├── otp.service.ts
│   │   ├── leadApigateway.service.ts
│   │   ├── axios.service.ts
│   │   └── cronJobs/cronJobs.service.ts
│   ├── database/
│   │   ├── entity/            — TypeORM entities (MySQL DSA DB + Ramfin DB)
│   │   └── repository/        — TypeORM repository wrappers
│   ├── middlewares/           — auth, validation, encryption, error, response, context
│   ├── consumer/
│   │   ├── router.ts          — SQS message dispatcher
│   │   └── processors/        — dsaUserwiseReport.processor.ts
│   └── redis/                 — ioredis client + cache service
│
├── External Services
│   ├── MySQL (primary DSA DB) — via TypeORM AppDataSource
│   ├── MySQL (Ramfin DB)      — via TypeORM AppDataSourceRamfin (separate DataSource)
│   ├── Redis                  — ioredis; used for caching (credentials, UTM, etc.)
│   ├── AWS S3                 — file upload/download, presigned URLs
│   ├── AWS SES                — email sending
│   ├── AWS SQS                — async job queue (lead download reports)
│   └── External Lead API      — leadApigateway.service (HTTP via axios)
│
└── Request Lifecycle
    1. Request → context middleware (CLS) → auth middleware → validation middleware
    2. → Controller → Service → Repository → DB/S3/SQS
    3. → response.middleware (custom success/failure/encrypt helpers) → client
    SQS Consumer Lifecycle: poll SQS → consumer/router.ts → processor → DsaService
```

## DSA-Backend.raw

```
DSA-Backend (Express/TypeScript Node.js service)
├── Entry Points
│   ├── src/server.ts          — HTTP server (registers all routes, boots App)
│   └── src/consumer.ts        — SQS consumer (separate process, polls queue)
│
├── src/app.ts                 — Express App class: middleware, routes, DB init, cron, swagger
│
├── Top-level Modules
│   ├── routes/                — Route definitions (auth, dsa, media, user, index)
│   ├── controllers/           — Request handlers (auth, dsa, media, users, index)
│   ├── services/              — Business logic
│   │   ├── auth.service.ts
│   │   ├── users.service.ts
│   │   ├── dsa.service.ts
│   │   ├── s3MediaUpload.service.ts
│   │   ├── otp.service.ts
│   │   ├── leadApigateway.service.ts
│   │   ├── axios.service.ts
│   │   └── cronJobs/cronJobs.service.ts
│   ├── database/
│   │   ├── entity/            — TypeORM entities (MySQL DSA DB + Ramfin DB)
│   │   └── repository/        — TypeORM repository wrappers
│   ├── middlewares/           — auth, validation, encryption, error, response, context
│   ├── consumer/
│   │   ├── router.ts          — SQS message dispatcher
│   │   └── processors/        — dsaUserwiseReport.processor.ts
│   └── redis/                 — ioredis client + cache service
│
├── External Services
│   ├── MySQL (primary DSA DB) — via TypeORM AppDataSource
│   ├── MySQL (Ramfin DB)      — via TypeORM AppDataSourceRamfin (separate DataSource)
│   ├── Redis                  — ioredis; used for caching (credentials, UTM, etc.)
│   ├── AWS S3                 — file upload/download, presigned URLs
│   ├── AWS SES                — email sending
│   ├── AWS SQS                — async job queue (lead download reports)
│   └── External Lead API      — leadApigateway.service (HTTP via axios)
│
└── Request Lifecycle
    1. Request → context middleware (CLS) → auth middleware → validation middleware
    2. → Controller → Service → Repository → DB/S3/SQS
    3. → response.middleware (custom success/failure/encrypt helpers) → client
    SQS Consumer Lifecycle: poll SQS → consumer/router.ts → processor → DsaService
```

## Kamakshimoney-onboarding

**Type:** React SPA (Single Page Application) — loan onboarding frontend for Kamakshi Money.

**Entry Points:**
- `index.html` → `src/main.jsx` (bootstraps React, Redux store, Google OAuth provider, CleverTap)
- `src/App.jsx` → `src/routes/AppRoutes.jsx` (root routing)

**Top-level Modules:**
```
src/
├── main.jsx              — App bootstrap, Redux Provider, Google OAuth, CleverTap init
├── App.jsx               — Root component
├── routes/
│   ├── AppRoutes.jsx     — All route definitions (lazy-loaded pages)
│   └── ProtectedRoutes.jsx — Auth guard wrapper
├── pages/                — 28 page-level components (one per onboarding step)
├── components/           — Reusable UI components (forms, shared, feature-specific)
├── redux/
│   ├── store.js          — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js   — UI state (loading, stepper, install prompt)
│       └── userSlice.js  — User/loan journey state
├── services/
│   ├── userService.js    — All API call functions (backend REST calls via axios)
│   └── dashboardService.js — Empty/placeholder
├── utils/
│   ├── apiClient.js      — Axios wrapper (callApi)
│   ├── encryption.js     — AES decryption utility
│   ├── storage.js        — localStorage abstraction
│   ├── helper.js         — Utility functions
│   └── lazyWithRetry.js  — Lazy import with retry
├── events/
│   └── clevertapEvents.js — CleverTap event push functions
├── lib/
│   ├── clevertap.js      — CleverTap SDK init
│   └── razorpay.js       — Razorpay e-mandate integration
└── hooks/                — Custom hooks (stepper, toast, page tracking, back-button)
```

**External Services:**
- **Backend REST API** — via `apiClient.js` (base URL from env vars)
- **CleverTap** — analytics/event tracking (`clevertap-web-sdk`)
- **Google OAuth** — `@react-oauth/google`, `googleAuthAPI`
- **Razorpay** — e-mandate payment flow (`src/lib/razorpay.js`)
- **HyperVerge** — selfie/KYC verification (`SelfieHyperVerge.jsx`)
- **Finbox** — bank statement/banking surrogate (`Finbox.jsx`)
- **Digilocker** — Aadhaar KYC (`DigilockerVerify.jsx`)
- **Google Analytics (GA4)** — `gtag` in `index.html`
- **Meta Pixel** — `fbq` in `index.html`
- **Microsoft Clarity** — script in `index.html`
- **AWS S3 + CloudFront** — production hosting (deploy workflow)

**Core Loan Onboarding Flow (page sequence):**
Login → PANVerify → EmploymentDetails → SelectTenure → LoanApproval → YourEmail → AadhaarVerification → CameraPermission → Selfie/SelfieHyperVerge → AddBankAccount → ConfirmBankAccount → Emandate → PennyDrop → KFS → Disbursed

---

## Kamakshimoney-onboarding.raw

**Type:** React SPA (Single Page Application) — loan onboarding frontend for Kamakshi Money.

**Entry Points:**
- `index.html` → `src/main.jsx` (bootstraps React, Redux store, Google OAuth provider, CleverTap)
- `src/App.jsx` → `src/routes/AppRoutes.jsx` (root routing)

**Top-level Modules:**
```
src/
├── main.jsx              — App bootstrap, Redux Provider, Google OAuth, CleverTap init
├── App.jsx               — Root component
├── routes/
│   ├── AppRoutes.jsx     — All route definitions (lazy-loaded pages)
│   └── ProtectedRoutes.jsx — Auth guard wrapper
├── pages/                — 28 page-level components (one per onboarding step)
├── components/           — Reusable UI components (forms, shared, feature-specific)
├── redux/
│   ├── store.js          — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js   — UI state (loading, stepper, install prompt)
│       └── userSlice.js  — User/loan journey state
├── services/
│   ├── userService.js    — All API call functions (backend REST calls via axios)
│   └── dashboardService.js — Empty/placeholder
├── utils/
│   ├── apiClient.js      — Axios wrapper (callApi)
│   ├── encryption.js     — AES decryption utility
│   ├── storage.js        — localStorage abstraction
│   ├── helper.js         — Utility functions
│   └── lazyWithRetry.js  — Lazy import with retry
├── events/
│   └── clevertapEvents.js — CleverTap event push functions
├── lib/
│   ├── clevertap.js      — CleverTap SDK init
│   └── razorpay.js       — Razorpay e-mandate integration
└── hooks/                — Custom hooks (stepper, toast, page tracking, back-button)
```

**External Services:**
- **Backend REST API** — via `apiClient.js` (base URL from env vars)
- **CleverTap** — analytics/event tracking (`clevertap-web-sdk`)
- **Google OAuth** — `@react-oauth/google`, `googleAuthAPI`
- **Razorpay** — e-mandate payment flow (`src/lib/razorpay.js`)
- **HyperVerge** — selfie/KYC verification (`SelfieHyperVerge.jsx`)
- **Finbox** — bank statement/banking surrogate (`Finbox.jsx`)
- **Digilocker** — Aadhaar KYC (`DigilockerVerify.jsx`)
- **Google Analytics (GA4)** — `gtag` in `index.html`
- **Meta Pixel** — `fbq` in `index.html`
- **Microsoft Clarity** — script in `index.html`
- **AWS S3 + CloudFront** — production hosting (deploy workflow)

**Core Loan Onboarding Flow (page sequence):**
Login → PANVerify → EmploymentDetails → SelectTenure → LoanApproval → YourEmail → AadhaarVerification → CameraPermission → Selfie/SelfieHyperVerge → AddBankAccount → ConfirmBankAccount → Emandate → PennyDrop → KFS → Disbursed

---

## crm-kamakshimoney-frontend

**Entry Points**
- `src/index.js` — React app bootstrap, mounts `<App />`
- `src/App.js` — Root component, wraps router and Redux provider
- `src/routes/AppRouter.js` — Top-level router (authentication guard)
- `src/routes/Router.js` — Lazy-loaded route definitions for all pages

**Top-Level Modules**
```
src/
├── pages/          — Feature pages (40+ modules, each with sub-components)
├── components/     — Shared/reusable UI components
├── services/       — API service classes (extend BaseAPI)
├── redux/          — Redux Toolkit store, slices, middleware
├── hooks/          — Custom React hooks
├── hoc/            — Higher-order components (permissions)
├── lib/            — File download helpers, generic helpers
├── utils/          — API fetch wrapper, storage, environment, auto-logout
├── validation/     — Yup validation schemas
├── constants/      — Dropdowns, menus, master data, endpoints
└── scss/           — Global SCSS design tokens and utilities
```

**Service Layer (all extend `BaseAPI`)**
- `AdminAPI`, `AuthAPI`, `AppFunctionManagementAPI`, `CollectionAPI`, `CollectionSettingAPI`
- `CommonAPI`, `CRMManagementAPI`, `CustomerProfileAPI`, `DashboardAPI`
- `Disbursal`, `LeadActions`, `LeadsAPI`, `LogsAPI`, `QuickReportAPI`, `RefundAPI`, `ReportAPI`
- `upload-api.js` — standalone upload functions

**State Management**
- Redux Toolkit + redux-persist (`localStorage`, `user` slice persisted)
- Slices: `userSlice`, `appSlice`, `navbarSlice`, `paginationSlice`, `apiSlice`

**External Services**
- Backend REST API (URL from `src/utils/environment.js`)
- AWS S3 — file uploads and downloads (refund CSV, manual disbursal)
- AWS CloudFront — CDN for built assets (`E3KVVACOIT7Q7W`)
- Razorpay — payment/disbursal updates
- Kaleyra — SMS/call logs
- SendInBlue — email logs
- Whatsapp API — messaging logs

**Core Request Lifecycle**
1. Component mounts → calls service method (e.g., `CollectionAPI.fetchXxx()`)
2. Service `makeRequest()` in `BaseAPI` calls `utils/api.js` (`apiData()`) via Axios
3. Response dispatched to Redux slice or set in local state
4. Pagination updated via `paginationSlice`; errors shown via `react-toastify`

**CI/CD**
- GitHub Actions (`deploy-main.yml`): `npm build` → `aws s3 cp` → CloudFront invalidation on push to `main`

---

## crm-kamakshimoney-frontend.raw

**Entry Points**
- `src/index.js` — React app bootstrap, mounts `<App />`
- `src/App.js` — Root component, wraps router and Redux provider
- `src/routes/AppRouter.js` — Top-level router (authentication guard)
- `src/routes/Router.js` — Lazy-loaded route definitions for all pages

**Top-Level Modules**
```
src/
├── pages/          — Feature pages (40+ modules, each with sub-components)
├── components/     — Shared/reusable UI components
├── services/       — API service classes (extend BaseAPI)
├── redux/          — Redux Toolkit store, slices, middleware
├── hooks/          — Custom React hooks
├── hoc/            — Higher-order components (permissions)
├── lib/            — File download helpers, generic helpers
├── utils/          — API fetch wrapper, storage, environment, auto-logout
├── validation/     — Yup validation schemas
├── constants/      — Dropdowns, menus, master data, endpoints
└── scss/           — Global SCSS design tokens and utilities
```

**Service Layer (all extend `BaseAPI`)**
- `AdminAPI`, `AuthAPI`, `AppFunctionManagementAPI`, `CollectionAPI`, `CollectionSettingAPI`
- `CommonAPI`, `CRMManagementAPI`, `CustomerProfileAPI`, `DashboardAPI`
- `Disbursal`, `LeadActions`, `LeadsAPI`, `LogsAPI`, `QuickReportAPI`, `RefundAPI`, `ReportAPI`
- `upload-api.js` — standalone upload functions

**State Management**
- Redux Toolkit + redux-persist (`localStorage`, `user` slice persisted)
- Slices: `userSlice`, `appSlice`, `navbarSlice`, `paginationSlice`, `apiSlice`

**External Services**
- Backend REST API (URL from `src/utils/environment.js`)
- AWS S3 — file uploads and downloads (refund CSV, manual disbursal)
- AWS CloudFront — CDN for built assets (`E3KVVACOIT7Q7W`)
- Razorpay — payment/disbursal updates
- Kaleyra — SMS/call logs
- SendInBlue — email logs
- Whatsapp API — messaging logs

**Core Request Lifecycle**
1. Component mounts → calls service method (e.g., `CollectionAPI.fetchXxx()`)
2. Service `makeRequest()` in `BaseAPI` calls `utils/api.js` (`apiData()`) via Axios
3. Response dispatched to Redux slice or set in local state
4. Pagination updated via `paginationSlice`; errors shown via `react-toastify`

**CI/CD**
- GitHub Actions (`deploy-main.yml`): `npm build` → `aws s3 cp` → CloudFront invalidation on push to `main`

---

## crm-react

React 18 SPA (Create React App), deployed to AWS S3 + CloudFront.

```
src/
├── index.js                   Entry point — mounts <App /> with Redux Provider
├── App.js                     Root component — wraps AppRouter
├── routes/
│   ├── AppRouter.js           Top-level router (auth guards, layout wrapper)
│   └── Router.js              Lazy-loaded route definitions for all pages
├── layout/
│   └── Layout.js              Sidebar (Navbar) + Header shell
├── pages/                     Feature pages (grouped by domain)
│   ├── Authentication/        Login, Logout, VerifyOTP, ForgotPassword, ChangePassword, AutoLogin
│   ├── Dashboard/
│   ├── Leads/                 AllLeads, CreditLeads, HotLeads, SanctionLeads
│   ├── CustomerProfile/       UserInfo, LoanApplication, Collection, Communication, Documents, HistoricalData, TimeLine, ApiLogs
│   ├── Collection/            PendingCollection, Closed, Settled, PartPaid, DNDCustomer, AddNotRequired, BulkEmandate, WaivedOff, PaydayPaymentPendingEmi, Refund
│   ├── CollectionManager/     ApprovalPending, Approved, Rejected, OnlinePayments, BulkUpload
│   ├── CollectionSetting/     SettlementReport
│   ├── Disbursal/             BankUpdate, BankUpdateRejected, Disbursed, ManualDisbursal
│   ├── CRMManagement/         Users, Logins, Roles, Permissions, IPWhiteListing, SourcingPartners, DSAPartner, UserListAdd/Update/Access, HavePermission
│   ├── Logs/                  APILogs, AppInstallations, ChatLogs, DialerLogs, KaleyraLogs, RazorpayLogs, SendInBlueLogs, WhatsappLogs
│   ├── Reports/               ~20 report pages (quick, date-wise, disbursal, collection, etc.)
│   ├── AppFunctionManagement/ AutoDisbursalStatus, HolidayList, RepaymentGatewayType
│   ├── LeadActions/           ManualSelfieVerification/Confirmation, NameMismatchManager, PaymentModeManager, RepaymentDateManager
│   ├── Blacklisted/           BlacklistCustomers, BlacklistPancard
│   ├── Cibil/, Customers/, Feedback/, SecureDecryption/, CallbackRequest/
├── services/                  API layer — class-based, all extend BaseAPI
│   ├── BaseAPI.js             axios wrapper, error handling, auth token injection
│   ├── AuthAPI, AdminAPI, CustomerProfileAPI, CollectionAPI, CollectionSettingAPI
│   ├── LeadsAPI, LeadActions, DashboardAPI, Disbursal, CRMManagementAPI
│   ├── AppFunctionManagementAPI, LogsAPI, ReportAPI, QuickReportAPI, RefundAPI
│   ├── CommonAPI, LentraAPI, upload-api.js
├── redux/
│   ├── store.js               Redux Toolkit store; redux-persist whitelist: ["user"]
│   └── slices/                userSlice, appSlice, paginationSlice, navbarSlice, apiSlice(s)
├── components/                Shared UI components (Header, Navbar, Loader, Pagination, Filter, etc.)
├── hooks/                     useFetchWithFilter, useResetPagination, useRouteCheck, useWindowSize
├── hoc/                       withDownloadPermission, withViewAccess
├── utils/                     api.js (axios), autoLogout.js, storage.js (token), environment.js
├── constants/                 dropdown.js, master.js, menu.js, report.js, endpoints.js
└── validation/                Yup schemas (Auth, CRMManagement, CustomerProfile, DndAdd, Leads)
```

**External services consumed:**
- Backend REST API (URL from `src/utils/environment.js`)
- AWS S3 (file uploads/downloads, static hosting)
- Razorpay (disbursal/payment status)
- Kaleyra (SMS/call logs)
- SendInBlue (email logs)
- AWS CloudFront (CDN/invalidation on deploy)

**Core lifecycle:** User authenticates → token stored in localStorage via `storage.js` → persisted in Redux `userSlice` → `AppRouter` checks auth → `Layout` renders sidebar + header → page components call service class methods → results stored locally in component state or Redux slices → `paginationSlice` drives paginated tables → `autoLogout` monitors inactivity.

---

## crm-react.raw

React 18 SPA (Create React App), deployed to AWS S3 + CloudFront.

```
src/
├── index.js                   Entry point — mounts <App /> with Redux Provider
├── App.js                     Root component — wraps AppRouter
├── routes/
│   ├── AppRouter.js           Top-level router (auth guards, layout wrapper)
│   └── Router.js              Lazy-loaded route definitions for all pages
├── layout/
│   └── Layout.js              Sidebar (Navbar) + Header shell
├── pages/                     Feature pages (grouped by domain)
│   ├── Authentication/        Login, Logout, VerifyOTP, ForgotPassword, ChangePassword, AutoLogin
│   ├── Dashboard/
│   ├── Leads/                 AllLeads, CreditLeads, HotLeads, SanctionLeads
│   ├── CustomerProfile/       UserInfo, LoanApplication, Collection, Communication, Documents, HistoricalData, TimeLine, ApiLogs
│   ├── Collection/            PendingCollection, Closed, Settled, PartPaid, DNDCustomer, AddNotRequired, BulkEmandate, WaivedOff, PaydayPaymentPendingEmi, Refund
│   ├── CollectionManager/     ApprovalPending, Approved, Rejected, OnlinePayments, BulkUpload
│   ├── CollectionSetting/     SettlementReport
│   ├── Disbursal/             BankUpdate, BankUpdateRejected, Disbursed, ManualDisbursal
│   ├── CRMManagement/         Users, Logins, Roles, Permissions, IPWhiteListing, SourcingPartners, DSAPartner, UserListAdd/Update/Access, HavePermission
│   ├── Logs/                  APILogs, AppInstallations, ChatLogs, DialerLogs, KaleyraLogs, RazorpayLogs, SendInBlueLogs, WhatsappLogs
│   ├── Reports/               ~20 report pages (quick, date-wise, disbursal, collection, etc.)
│   ├── AppFunctionManagement/ AutoDisbursalStatus, HolidayList, RepaymentGatewayType
│   ├── LeadActions/           ManualSelfieVerification/Confirmation, NameMismatchManager, PaymentModeManager, RepaymentDateManager
│   ├── Blacklisted/           BlacklistCustomers, BlacklistPancard
│   ├── Cibil/, Customers/, Feedback/, SecureDecryption/, CallbackRequest/
├── services/                  API layer — class-based, all extend BaseAPI
│   ├── BaseAPI.js             axios wrapper, error handling, auth token injection
│   ├── AuthAPI, AdminAPI, CustomerProfileAPI, CollectionAPI, CollectionSettingAPI
│   ├── LeadsAPI, LeadActions, DashboardAPI, Disbursal, CRMManagementAPI
│   ├── AppFunctionManagementAPI, LogsAPI, ReportAPI, QuickReportAPI, RefundAPI
│   ├── CommonAPI, LentraAPI, upload-api.js
├── redux/
│   ├── store.js               Redux Toolkit store; redux-persist whitelist: ["user"]
│   └── slices/                userSlice, appSlice, paginationSlice, navbarSlice, apiSlice(s)
├── components/                Shared UI components (Header, Navbar, Loader, Pagination, Filter, etc.)
├── hooks/                     useFetchWithFilter, useResetPagination, useRouteCheck, useWindowSize
├── hoc/                       withDownloadPermission, withViewAccess
├── utils/                     api.js (axios), autoLogout.js, storage.js (token), environment.js
├── constants/                 dropdown.js, master.js, menu.js, report.js, endpoints.js
└── validation/                Yup schemas (Auth, CRMManagement, CustomerProfile, DndAdd, Leads)
```

**External services consumed:**
- Backend REST API (URL from `src/utils/environment.js`)
- AWS S3 (file uploads/downloads, static hosting)
- Razorpay (disbursal/payment status)
- Kaleyra (SMS/call logs)
- SendInBlue (email logs)
- AWS CloudFront (CDN/invalidation on deploy)

**Core lifecycle:** User authenticates → token stored in localStorage via `storage.js` → persisted in Redux `userSlice` → `AppRouter` checks auth → `Layout` renders sidebar + header → page components call service class methods → results stored locally in component state or Redux slices → `paginationSlice` drives paginated tables → `autoLogout` monitors inactivity.

---

## devOpsStack

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

## devOpsStack.raw

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

## kanakloans-webview

**Entry Points**
- `index.html` — single HTML shell, mounts React app at `#root`
- `src/main.jsx` — bootstraps React, wraps app with Redux Provider, Google OAuth Provider, initializes CleverTap

**Top-Level Module Tree**
```
src/
├── App.jsx                  — root component, renders AppRoutes
├── routes/
│   ├── AppRoutes.jsx        — React Router route definitions, InactivityLogout wrapper
│   └── ProtectedRoutes.jsx  — auth guard for protected pages
├── pages/                   — one component per route/screen (30+ pages)
├── components/              — reusable UI components (forms, shared, feature drawers)
├── redux/
│   ├── store.js             — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js      — loading, stepper, install state
│       └── userSlice.js     — mobile, customer, lead, employment, loan offer state
├── services/
│   └── userService.js       — all API call functions (axios via apiClient)
├── utils/
│   ├── apiClient.js         — axios wrapper (`callApi`)
│   ├── storage.js           — localStorage utility + KEYS constants
│   ├── encryption.js        — AES decryption utility
│   ├── helper.js            — misc helpers (delay, UTM, Google Events, redirect)
│   └── handleRedirectionAfterLogin.js — post-login routing logic
├── hooks/                   — useToast, useStepper, usePageTracking, useBackButtonLogout
├── events/clevertapEvents.js — CleverTap event push wrappers
└── lib/
    ├── clevertap.js         — CleverTap SDK init
    └── razorpay.js          — Razorpay e-mandate integration
```

**External Services**
- **Backend REST API** — called via `src/utils/apiClient.js` (base URL from env)
- **CleverTap** — analytics/event tracking (`clevertap-web-sdk`)
- **Google OAuth** — `@react-oauth/google`, used for login and email pre-fill
- **Razorpay** — e-mandate payment flow (`src/lib/razorpay.js`)
- **HyperVerge** — selfie/KYC SDK (loaded dynamically in `SelfieHyperVerge.jsx`)
- **Finbox** — bank statement fetching (`src/pages/Finbox.jsx`)
- **Digilocker** — Aadhaar KYC redirect flow
- **Google Analytics (GA4)** — `gtag` via `index.html` + `trackG4Events` helper
- **Microsoft Clarity** — session recording, injected in `index.html`
- **AWS S3 + CloudFront** — static hosting (deployed via CI/CD)

**Core Request Lifecycle**
1. User visits SPA → `AppRoutes` resolves path → `ProtectedRoutes` checks auth token from localStorage
2. Page component calls service functions in `userService.js` → `callApi` (axios) → backend REST API
3. Responses update Redux slices (`userSlice`, `appSlice`) persisted via `redux-persist`
4. Navigation proceeds through loan journey steps; `stepCheckerAPI` determines current route on reload

---

## kanakloans-webview.raw

**Entry Points**
- `index.html` — single HTML shell, mounts React app at `#root`
- `src/main.jsx` — bootstraps React, wraps app with Redux Provider, Google OAuth Provider, initializes CleverTap

**Top-Level Module Tree**
```
src/
├── App.jsx                  — root component, renders AppRoutes
├── routes/
│   ├── AppRoutes.jsx        — React Router route definitions, InactivityLogout wrapper
│   └── ProtectedRoutes.jsx  — auth guard for protected pages
├── pages/                   — one component per route/screen (30+ pages)
├── components/              — reusable UI components (forms, shared, feature drawers)
├── redux/
│   ├── store.js             — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js      — loading, stepper, install state
│       └── userSlice.js     — mobile, customer, lead, employment, loan offer state
├── services/
│   └── userService.js       — all API call functions (axios via apiClient)
├── utils/
│   ├── apiClient.js         — axios wrapper (`callApi`)
│   ├── storage.js           — localStorage utility + KEYS constants
│   ├── encryption.js        — AES decryption utility
│   ├── helper.js            — misc helpers (delay, UTM, Google Events, redirect)
│   └── handleRedirectionAfterLogin.js — post-login routing logic
├── hooks/                   — useToast, useStepper, usePageTracking, useBackButtonLogout
├── events/clevertapEvents.js — CleverTap event push wrappers
└── lib/
    ├── clevertap.js         — CleverTap SDK init
    └── razorpay.js          — Razorpay e-mandate integration
```

**External Services**
- **Backend REST API** — called via `src/utils/apiClient.js` (base URL from env)
- **CleverTap** — analytics/event tracking (`clevertap-web-sdk`)
- **Google OAuth** — `@react-oauth/google`, used for login and email pre-fill
- **Razorpay** — e-mandate payment flow (`src/lib/razorpay.js`)
- **HyperVerge** — selfie/KYC SDK (loaded dynamically in `SelfieHyperVerge.jsx`)
- **Finbox** — bank statement fetching (`src/pages/Finbox.jsx`)
- **Digilocker** — Aadhaar KYC redirect flow
- **Google Analytics (GA4)** — `gtag` via `index.html` + `trackG4Events` helper
- **Microsoft Clarity** — session recording, injected in `index.html`
- **AWS S3 + CloudFront** — static hosting (deployed via CI/CD)

**Core Request Lifecycle**
1. User visits SPA → `AppRoutes` resolves path → `ProtectedRoutes` checks auth token from localStorage
2. Page component calls service functions in `userService.js` → `callApi` (axios) → backend REST API
3. Responses update Redux slices (`userSlice`, `appSlice`) persisted via `redux-persist`
4. Navigation proceeds through loan journey steps; `stepCheckerAPI` determines current route on reload

---

## node-crm

**Entry Points**
- `src/server.ts` → instantiates `App` with all routes
- `src/start.ts` → application bootstrapper
- `src/app.ts` → Express app: middleware, routes, Swagger, error handling, cron jobs

**Top-Level Modules**
```
src/
├── app.ts                  # Express App class
├── routes/index.ts         # Route aggregator (all route modules)
├── controllers/            # Request handlers (~30 controllers)
├── services/               # Business logic (~70 services)
│   ├── cronJobs/           # Cron job services (bulk mandate, WebEngage, loan write-off)
│   └── thirdParty/         # DigiLocker, Digitap, Finbox, S3, Surepass
├── database/
│   ├── mysql/              # Knex-based model classes (~80 tables)
│   ├── mongo/              # Mongoose models (KaleyraLogs, EmiAutoPaymentCronLog, RazorpayRefundLogs, RazorpayWebhookLogs, User, CustomerAssetData)
│   └── prisma/schema.prisma
├── middlewares/            # Auth, error, validation, pagination, permission
├── validations/            # Joi schemas
├── interfaces/             # TypeScript interfaces
├── enums/                  # Enums
└── utils/                  # Logger, MySQL/Mongo connections, encryption, Razorpay client
```

**External Services**
- **MySQL** (primary + replica) — via Knex (`src/utils/mysql.ts`)
- **MongoDB** — via Mongoose (`src/utils/mongo.ts`)
- **Redis** — via ioredis (`src/utils/ioredis.utils.ts`); also used for Bull queues (`src/queues/`)
- **AWS S3 + SES** (`src/services/thirdParty/s3.service.ts`)
- **Razorpay** (payments, mandates, payouts, subscriptions)
- **Surepass** (PAN/Aadhaar verification)
- **Digitap** (face liveness)
- **Finbox** (bank connect / statement analysis)
- **DigiLocker** (Aadhaar via DigiLocker)
- **Firebase** (push notifications)
- **MSG91 / Kaleyra / Sendinblue** (SMS/email)
- **Sentry** (`src/sentry.ts`) — error monitoring

**Request Lifecycle**
`HTTP request → Express middleware (auth, pagination, validation) → Controller → Service → MySQL/MongoDB/External API → Response`

**Cron Jobs** (started in `App.startCronJobs()`): bulk emandate, loan write-off, DSA cron, contact-us Excel, WebEngage sync.

---

## node-crm.raw

**Entry Points**
- `src/server.ts` → instantiates `App` with all routes
- `src/start.ts` → application bootstrapper
- `src/app.ts` → Express app: middleware, routes, Swagger, error handling, cron jobs

**Top-Level Modules**
```
src/
├── app.ts                  # Express App class
├── routes/index.ts         # Route aggregator (all route modules)
├── controllers/            # Request handlers (~30 controllers)
├── services/               # Business logic (~70 services)
│   ├── cronJobs/           # Cron job services (bulk mandate, WebEngage, loan write-off)
│   └── thirdParty/         # DigiLocker, Digitap, Finbox, S3, Surepass
├── database/
│   ├── mysql/              # Knex-based model classes (~80 tables)
│   ├── mongo/              # Mongoose models (KaleyraLogs, EmiAutoPaymentCronLog, RazorpayRefundLogs, RazorpayWebhookLogs, User, CustomerAssetData)
│   └── prisma/schema.prisma
├── middlewares/            # Auth, error, validation, pagination, permission
├── validations/            # Joi schemas
├── interfaces/             # TypeScript interfaces
├── enums/                  # Enums
└── utils/                  # Logger, MySQL/Mongo connections, encryption, Razorpay client
```

**External Services**
- **MySQL** (primary + replica) — via Knex (`src/utils/mysql.ts`)
- **MongoDB** — via Mongoose (`src/utils/mongo.ts`)
- **Redis** — via ioredis (`src/utils/ioredis.utils.ts`); also used for Bull queues (`src/queues/`)
- **AWS S3 + SES** (`src/services/thirdParty/s3.service.ts`)
- **Razorpay** (payments, mandates, payouts, subscriptions)
- **Surepass** (PAN/Aadhaar verification)
- **Digitap** (face liveness)
- **Finbox** (bank connect / statement analysis)
- **DigiLocker** (Aadhaar via DigiLocker)
- **Firebase** (push notifications)
- **MSG91 / Kaleyra / Sendinblue** (SMS/email)
- **Sentry** (`src/sentry.ts`) — error monitoring

**Request Lifecycle**
`HTTP request → Express middleware (auth, pagination, validation) → Controller → Service → MySQL/MongoDB/External API → Response`

**Cron Jobs** (started in `App.startCronJobs()`): bulk emandate, loan write-off, DSA cron, contact-us Excel, WebEngage sync.

---

## node_crm

**Entry Points**
- `src/server.ts` → instantiates `App` class with all routes
- `src/start.ts` → application bootstrap
- `src/app.ts` → Express `App` class: middleware, routing, Sentry, cron jobs

**Top-Level Modules**
```
src/
├── app.ts               # Express app factory
├── server.ts            # Entry point wiring
├── routes/index.ts      # Route aggregation (29 route modules)
├── controllers/         # 30+ controller classes (thin HTTP handlers)
├── services/            # Business logic (80+ service classes)
│   ├── cronJobs/        # CronJobService (bulk mandate, loan write-off, DSA, NOC)
│   └── thirdParty/      # Digilocker, Digitap, Finbox, S3, SurePass
├── database/
│   ├── mysql/           # 80+ Knex model classes (active ORM layer)
│   ├── mongo/           # 5 Mongoose models + 3 repos
│   └── prisma/          # schema.prisma (MySQL, User model only)
├── middlewares/         # auth, error, multer, pagination, permission, validation
├── queues/              # Bull queue via ioredis
└── utils/               # AES/RSA encryption, Razorpay client, MySQL/Mongo conn
```

**External Services**
- **MySQL** (primary + read-replica) via Knex (`src/utils/mysql.ts`)
- **MongoDB** via Mongoose (`src/utils/mongo.ts`) — Kaleyra logs, EMI cron logs, Razorpay webhook/refund logs, user assets
- **Redis** (ioredis) — caching + Bull job queues
- **AWS S3 + SES** (`src/services/thirdParty/s3.service.ts`)
- **Razorpay** — payments, subscriptions, mandates, payouts (`src/utils/razorpayClient.utils.ts`)
- **Sentry** (`src/sentry.ts`) — error monitoring
- **Finbox**, **Digitap**, **Digilocker**, **SurePass** — KYC/banking
- **Firebase** (`src/services/firebase.service.ts`) — push notifications
- **WebEngage** — user events/analytics
- **Kaleyra / MSG91** — SMS OTP
- **Nodemailer / SendInBlue / AWS SES** — email

**Request Lifecycle**: `HTTP → Express middleware (auth JWT, permission check, Joi validation, pagination) → Controller → Service → Knex/Mongoose model → DB/External API → Response`

**Cron Jobs** started in `App.startCronJobs()`: bulk e-mandate, monthly loan write-off, DSA lead push, NOC doc sending, contact-us Excel.

---

## node_crm.raw

**Entry Points**
- `src/server.ts` → instantiates `App` class with all routes
- `src/start.ts` → application bootstrap
- `src/app.ts` → Express `App` class: middleware, routing, Sentry, cron jobs

**Top-Level Modules**
```
src/
├── app.ts               # Express app factory
├── server.ts            # Entry point wiring
├── routes/index.ts      # Route aggregation (29 route modules)
├── controllers/         # 30+ controller classes (thin HTTP handlers)
├── services/            # Business logic (80+ service classes)
│   ├── cronJobs/        # CronJobService (bulk mandate, loan write-off, DSA, NOC)
│   └── thirdParty/      # Digilocker, Digitap, Finbox, S3, SurePass
├── database/
│   ├── mysql/           # 80+ Knex model classes (active ORM layer)
│   ├── mongo/           # 5 Mongoose models + 3 repos
│   └── prisma/          # schema.prisma (MySQL, User model only)
├── middlewares/         # auth, error, multer, pagination, permission, validation
├── queues/              # Bull queue via ioredis
└── utils/               # AES/RSA encryption, Razorpay client, MySQL/Mongo conn
```

**External Services**
- **MySQL** (primary + read-replica) via Knex (`src/utils/mysql.ts`)
- **MongoDB** via Mongoose (`src/utils/mongo.ts`) — Kaleyra logs, EMI cron logs, Razorpay webhook/refund logs, user assets
- **Redis** (ioredis) — caching + Bull job queues
- **AWS S3 + SES** (`src/services/thirdParty/s3.service.ts`)
- **Razorpay** — payments, subscriptions, mandates, payouts (`src/utils/razorpayClient.utils.ts`)
- **Sentry** (`src/sentry.ts`) — error monitoring
- **Finbox**, **Digitap**, **Digilocker**, **SurePass** — KYC/banking
- **Firebase** (`src/services/firebase.service.ts`) — push notifications
- **WebEngage** — user events/analytics
- **Kaleyra / MSG91** — SMS OTP
- **Nodemailer / SendInBlue / AWS SES** — email

**Request Lifecycle**: `HTTP → Express middleware (auth JWT, permission check, Joi validation, pagination) → Controller → Service → Knex/Mongoose model → DB/External API → Response`

**Cron Jobs** started in `App.startCronJobs()`: bulk e-mandate, monthly loan write-off, DSA lead push, NOC doc sending, contact-us Excel.

---

## onboarding-service-frontend

**Entry Point:** `src/main.jsx` → mounts React app with Redux `<Provider>`, `<PersistGate>`, Google OAuth `<GoogleOAuthProvider>`, and registers PWA service worker.

**Top-level modules:**
```
src/
├── main.jsx                  # App bootstrap, Redux/Google/PWA init
├── App.jsx                   # Root component, wraps AppRoutes
├── routes/
│   ├── AppRoutes.jsx         # React Router route definitions, InactivityLogout
│   └── ProtectedRoutes.jsx   # Auth guard wrapper
├── pages/                    # Full-page route components (20+ pages)
├── components/               # Reusable UI components (forms, shared, modals)
├── redux/
│   ├── store.js              # Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js       # Global loading state, stepper flags, PWA trigger
│       └── userSlice.js      # Auth/session state (mobile, lead, customer, loan offer)
├── services/
│   └── userService.js        # All API call functions (axios via apiClient)
├── utils/
│   ├── apiClient.js          # Axios wrapper (callApi)
│   ├── encryption.js         # AES decrypt utility
│   ├── helper.js             # Delay, redirect, UTM, geolocation helpers
│   ├── storage.js            # localStorage wrapper + KEYS constants
│   └── validation.js         # Yup validation schemas
├── events/
│   └── clevertapEvents.js    # All CleverTap analytics event functions
├── i18n/                     # i18next config + en/hi/ka locale JSONs
├── lib/
│   ├── clevertap.js          # CleverTap SDK init
│   └── razorpay.js           # Razorpay e-mandate integration
└── hooks/                    # Custom React hooks
```

**External Services:**
- **Backend API** (`VITE_BASE_URL`) — Node.js onboarding API (loan journey steps)
- **PHP API** (`VITE_PHP_BASE_URL`) — legacy PHP backend
- **User Service** (`VITE_USER_SERVICE_BASE_URL`) — customer/auth service
- **Razorpay** — e-mandate payment
- **CleverTap** — analytics/event tracking
- **Digilocker / HyperVerge** — KYC verification
- **Finbox** — financial profile / bank statement analysis
- **Google OAuth** — email sign-in
- **AWS S3 + CloudFront** — static hosting (deployed via GitHub Actions)
- **Google Tag Manager / Meta Pixel / Microsoft Clarity** — analytics tags in `index.html`

**Core request lifecycle:** User action → Page component → `userService.js` function → `callApi()` (axios) → Backend API → Redux dispatch to update `userSlice`/`appSlice` → navigate to next route.

---

## onboarding-service-frontend.raw

**Entry Point:** `src/main.jsx` → mounts React app with Redux `<Provider>`, `<PersistGate>`, Google OAuth `<GoogleOAuthProvider>`, and registers PWA service worker.

**Top-level modules:**
```
src/
├── main.jsx                  # App bootstrap, Redux/Google/PWA init
├── App.jsx                   # Root component, wraps AppRoutes
├── routes/
│   ├── AppRoutes.jsx         # React Router route definitions, InactivityLogout
│   └── ProtectedRoutes.jsx   # Auth guard wrapper
├── pages/                    # Full-page route components (20+ pages)
├── components/               # Reusable UI components (forms, shared, modals)
├── redux/
│   ├── store.js              # Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js       # Global loading state, stepper flags, PWA trigger
│       └── userSlice.js      # Auth/session state (mobile, lead, customer, loan offer)
├── services/
│   └── userService.js        # All API call functions (axios via apiClient)
├── utils/
│   ├── apiClient.js          # Axios wrapper (callApi)
│   ├── encryption.js         # AES decrypt utility
│   ├── helper.js             # Delay, redirect, UTM, geolocation helpers
│   ├── storage.js            # localStorage wrapper + KEYS constants
│   └── validation.js         # Yup validation schemas
├── events/
│   └── clevertapEvents.js    # All CleverTap analytics event functions
├── i18n/                     # i18next config + en/hi/ka locale JSONs
├── lib/
│   ├── clevertap.js          # CleverTap SDK init
│   └── razorpay.js           # Razorpay e-mandate integration
└── hooks/                    # Custom React hooks
```

**External Services:**
- **Backend API** (`VITE_BASE_URL`) — Node.js onboarding API (loan journey steps)
- **PHP API** (`VITE_PHP_BASE_URL`) — legacy PHP backend
- **User Service** (`VITE_USER_SERVICE_BASE_URL`) — customer/auth service
- **Razorpay** — e-mandate payment
- **CleverTap** — analytics/event tracking
- **Digilocker / HyperVerge** — KYC verification
- **Finbox** — financial profile / bank statement analysis
- **Google OAuth** — email sign-in
- **AWS S3 + CloudFront** — static hosting (deployed via GitHub Actions)
- **Google Tag Manager / Meta Pixel / Microsoft Clarity** — analytics tags in `index.html`

**Core request lifecycle:** User action → Page component → `userService.js` function → `callApi()` (axios) → Backend API → Redux dispatch to update `userSlice`/`appSlice` → navigate to next route.

---

## onboarding-service

**Entry Points:**
- `src/server.ts` → creates `App` instance, starts HTTP server (port from env)
- `src/app.ts` → Express application setup, middleware registration, route mounting

**Top-level Modules:**
```
src/
├── routes/           → Route definitions (index.ts aggregates all routes)
├── controllers/      → HTTP request handlers
├── services/         → Business logic layer
│   └── thirdParty/   → External API integrations
├── database/
│   ├── mysql/        → Knex-based MySQL models (~100+ tables)
│   └── mongo/        → Mongoose models
├── middlewares/      → Auth, logging, step-checking, validation
├── config/           → DB, Redis, Sentry, env config
├── bull/producers/   → BullMQ job producers
├── redis/            → Redis client + cache service
└── utils/            → Helpers, logger, notifications, etc.
```

**Module Dependencies:**
- Controllers → Services → Database models
- Services call each other (e.g., `OnboardingService` calls `FinboxService`, `DecentroService`, `SurepassService`, etc.)
- Middlewares (auth, stepCheck) call services for validation before controllers execute

**External Services:**
- **Databases:** MySQL (Knex/Objection, primary + replica), MongoDB (Mongoose)
- **Cache/Queue:** Redis (ioredis), BullMQ
- **Payment:** Razorpay, PayU
- **KYC/Bureau:** Surepass, Digilocker/Decentro, Digitap, CIBIL, Experian, Finbox, Hyperverge, CKYC
- **Fraud Detection:** Fraudgator
- **Lending Core (LMS):** Lentra
- **Notifications:** Kaleyra (SMS/OTP), MSG91, AWS SES, Firebase, WhatsApp (Interakt)
- **Storage:** AWS S3
- **Monitoring:** Sentry, New Relic

**Request Lifecycle:**
1. Request → Express middleware (helmet, cors, body-parser, morgan)
2. → `saveApiLog` middleware → `auth.middleware` (JWT validation, customer attachment)
3. → `stepCheck2.middleware` (validates customer journey step)
4. → Controller handler → Service layer → DB models
5. → Response sent; `stepTrackerAfterResponse.middleware` saves step completion
6. → `eventLogs.middleware` fires async event logging (MySQL + MongoDB)

---

## onboarding_service_frontend

React 19 SPA (Vite build tool) for a loan onboarding journey targeting Ram Fincorp customers.

**Entry Points**
- `index.html` → `src/main.jsx` — mounts React app, wraps in Redux Provider, Google OAuth Provider, PWA service worker registration
- `src/App.jsx` — renders `AppRoutes`

**Top-Level Modules**
```
src/
├── main.jsx              — app bootstrap, Redux Provider, Google OAuth
├── App.jsx               — root component
├── routes/
│   ├── AppRoutes.jsx     — route definitions, InactivityLogout wrapper
│   └── ProtectedRoutes.jsx — auth guard (checks local storage token)
├── pages/                — 27 page-level components (one per loan journey step)
├── components/           — reusable UI (forms, shared layout, step-specific modals)
├── redux/
│   ├── store.js          — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js   — loading state, stepper, PWA install trigger
│       └── userSlice.js  — mobile, requestId, customer, lead, employment, loanOffer, accountId
├── services/
│   └── userService.js    — all API call functions (30+ functions over REST)
├── utils/
│   ├── apiClient.js      — axios wrapper (callApi)
│   ├── encryption.js     — AES decryption of API responses
│   ├── storage.js        — localStorage wrapper + KEYS constants
│   ├── helper.js         — delay, redirect, UTM, geolocation utilities
│   └── validation.js     — Yup schemas
├── events/
│   └── clevertapEvents.js — CleverTap analytics event push functions
├── lib/
│   ├── clevertap.js      — CleverTap SDK init
│   └── razorpay.js       — Razorpay e-mandate integration
└── i18n/                 — i18next, locales: en/hi/ka
```

**External Services**
- `VITE_BASE_URL` (Node onboarding API) — primary backend
- `VITE_PHP_BASE_URL` — legacy PHP backend
- `VITE_USER_SERVICE_BASE_URL` — user microservice
- Lentra API (`serviceurl.in`) — unclear purpose (CKYC/KYC)
- Razorpay — e-mandate payments
- CleverTap — analytics/event tracking
- Google OAuth — email sign-in
- Digilocker — KYC verification
- HyperVerge — selfie/liveness verification
- Finbox — bank account statement (AA flow)
- Google Analytics (gtag G-W55TK1ES3Z), Meta Pixel, Microsoft Clarity

**Core Request Lifecycle**
1. User navigates to a page → `ProtectedRoutes` checks JWT in localStorage
2. Page component calls service function → `callApi` (axios + optional delay) → backend REST API
3. Response dispatched to Redux slices; UI updates via selectors
4. CleverTap events fired at key journey milestones

---

## onboarding_service_frontend.raw

React 19 SPA (Vite build tool) for a loan onboarding journey targeting Ram Fincorp customers.

**Entry Points**
- `index.html` → `src/main.jsx` — mounts React app, wraps in Redux Provider, Google OAuth Provider, PWA service worker registration
- `src/App.jsx` — renders `AppRoutes`

**Top-Level Modules**
```
src/
├── main.jsx              — app bootstrap, Redux Provider, Google OAuth
├── App.jsx               — root component
├── routes/
│   ├── AppRoutes.jsx     — route definitions, InactivityLogout wrapper
│   └── ProtectedRoutes.jsx — auth guard (checks local storage token)
├── pages/                — 27 page-level components (one per loan journey step)
├── components/           — reusable UI (forms, shared layout, step-specific modals)
├── redux/
│   ├── store.js          — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js   — loading state, stepper, PWA install trigger
│       └── userSlice.js  — mobile, requestId, customer, lead, employment, loanOffer, accountId
├── services/
│   └── userService.js    — all API call functions (30+ functions over REST)
├── utils/
│   ├── apiClient.js      — axios wrapper (callApi)
│   ├── encryption.js     — AES decryption of API responses
│   ├── storage.js        — localStorage wrapper + KEYS constants
│   ├── helper.js         — delay, redirect, UTM, geolocation utilities
│   └── validation.js     — Yup schemas
├── events/
│   └── clevertapEvents.js — CleverTap analytics event push functions
├── lib/
│   ├── clevertap.js      — CleverTap SDK init
│   └── razorpay.js       — Razorpay e-mandate integration
└── i18n/                 — i18next, locales: en/hi/ka
```

**External Services**
- `VITE_BASE_URL` (Node onboarding API) — primary backend
- `VITE_PHP_BASE_URL` — legacy PHP backend
- `VITE_USER_SERVICE_BASE_URL` — user microservice
- Lentra API (`serviceurl.in`) — unclear purpose (CKYC/KYC)
- Razorpay — e-mandate payments
- CleverTap — analytics/event tracking
- Google OAuth — email sign-in
- Digilocker — KYC verification
- HyperVerge — selfie/liveness verification
- Finbox — bank account statement (AA flow)
- Google Analytics (gtag G-W55TK1ES3Z), Meta Pixel, Microsoft Clarity

**Core Request Lifecycle**
1. User navigates to a page → `ProtectedRoutes` checks JWT in localStorage
2. Page component calls service function → `callApi` (axios + optional delay) → backend REST API
3. Response dispatched to Redux slices; UI updates via selectors
4. CleverTap events fired at key journey milestones

---

## ramfin-report

```
ramfin-report (RamFin Reporting Service)
├── Entry Points
│   ├── src/start.ts          — process bootstrap
│   ├── src/server.ts         — instantiates App with all routes
│   └── src/app.ts            — Express App class; wires middleware, routes, DB connections
│
├── Config Layer
│   ├── src/config/default.ts         — default constants (IConfigApp)
│   ├── src/config/custom-environment-variables.ts — env var mappings
│   └── src/config.server.ts          — merges env vars into config singleton
│
├── Routes → Controllers → Services pattern
│   ├── routes/index.route.ts         — health/index
│   ├── routes/report.route.ts        — report endpoints
│   ├── routes/reportSummary.route.ts — report summary
│   ├── routes/quickReport.route.ts   — quick/async report download
│   └── routes/lead.route.ts          — lead modification report
│
├── Controllers (src/controllers/)
│   ├── index.controller.ts           — health check
│   ├── report.controller.ts          — sync report generation + Excel streaming
│   ├── reportSummary.controller.ts   — summary report
│   ├── quickReport.controller.ts     — queued async report download
│   ├── lead.controller.ts            — lead report endpoints
│   └── eventFunnel.controller.ts     — funnel analytics
│
├── Services (src/services/)
│   ├── report.service.ts             — all report query logic
│   ├── quickReport.service.ts        — quick report pagination, SQS job dispatch, S3 upload
│   ├── excelDownload.service.ts      — ExcelJS workbook generation
│   ├── lead.service.ts               — lead data queries
│   ├── loan.service.ts               — loan data, PDF generation (Puppeteer)
│   ├── emi.service.ts                — EMI calculation/queries
│   ├── credit.service.ts             — credit record management
│   ├── eventFunnel.service.ts        — funnel event queries
│   ├── notification.service.ts       — notification records
│   ├── teansections.services.ts      — transaction records
│   ├── api_req_res_log.service.ts    — API log persistence
│   ├── response.service.ts           — base response class
│   ├── api.service.ts                — Axios HTTP client wrapper
│   └── thirdParty/s3.service.ts      — AWS S3 + SES operations
│
├── Database Layer (src/database/)
│   ├── mysql/   — Knex-based model classes (primary + replica connections)
│   └── mongo/   — Mongoose model (OtpLogs)
│
├── Middlewares — auth (JWT), permission, pagination, validation (Joi), error, response
│
└── External Services
    ├── MySQL (primary + read replica)  — all core business data
    ├── MongoDB                          — OTP logs
    ├── AWS S3                           — report file storage, document storage
    ├── AWS SES                          — email sending
    └── AWS SQS                          — async quick-report job queue
```

Key lifecycle: HTTP request → Auth middleware → Permission check → Validation → Controller → Service → Knex/MySQL query or SQS dispatch → Excel/CSV/JSON response (or S3 upload + presigned URL).

---

## ramfin-report.raw

```
ramfin-report (RamFin Reporting Service)
├── Entry Points
│   ├── src/start.ts          — process bootstrap
│   ├── src/server.ts         — instantiates App with all routes
│   └── src/app.ts            — Express App class; wires middleware, routes, DB connections
│
├── Config Layer
│   ├── src/config/default.ts         — default constants (IConfigApp)
│   ├── src/config/custom-environment-variables.ts — env var mappings
│   └── src/config.server.ts          — merges env vars into config singleton
│
├── Routes → Controllers → Services pattern
│   ├── routes/index.route.ts         — health/index
│   ├── routes/report.route.ts        — report endpoints
│   ├── routes/reportSummary.route.ts — report summary
│   ├── routes/quickReport.route.ts   — quick/async report download
│   └── routes/lead.route.ts          — lead modification report
│
├── Controllers (src/controllers/)
│   ├── index.controller.ts           — health check
│   ├── report.controller.ts          — sync report generation + Excel streaming
│   ├── reportSummary.controller.ts   — summary report
│   ├── quickReport.controller.ts     — queued async report download
│   ├── lead.controller.ts            — lead report endpoints
│   └── eventFunnel.controller.ts     — funnel analytics
│
├── Services (src/services/)
│   ├── report.service.ts             — all report query logic
│   ├── quickReport.service.ts        — quick report pagination, SQS job dispatch, S3 upload
│   ├── excelDownload.service.ts      — ExcelJS workbook generation
│   ├── lead.service.ts               — lead data queries
│   ├── loan.service.ts               — loan data, PDF generation (Puppeteer)
│   ├── emi.service.ts                — EMI calculation/queries
│   ├── credit.service.ts             — credit record management
│   ├── eventFunnel.service.ts        — funnel event queries
│   ├── notification.service.ts       — notification records
│   ├── teansections.services.ts      — transaction records
│   ├── api_req_res_log.service.ts    — API log persistence
│   ├── response.service.ts           — base response class
│   ├── api.service.ts                — Axios HTTP client wrapper
│   └── thirdParty/s3.service.ts      — AWS S3 + SES operations
│
├── Database Layer (src/database/)
│   ├── mysql/   — Knex-based model classes (primary + replica connections)
│   └── mongo/   — Mongoose model (OtpLogs)
│
├── Middlewares — auth (JWT), permission, pagination, validation (Joi), error, response
│
└── External Services
    ├── MySQL (primary + read replica)  — all core business data
    ├── MongoDB                          — OTP logs
    ├── AWS S3                           — report file storage, document storage
    ├── AWS SES                          — email sending
    └── AWS SQS                          — async quick-report job queue
```

Key lifecycle: HTTP request → Auth middleware → Permission check → Validation → Controller → Service → Knex/MySQL query or SQS dispatch → Excel/CSV/JSON response (or S3 upload + presigned URL).

---

## ramfin_userservice

**Entry Points**
- `src/server.ts` — imports `App` and `routes` array, bootstraps the Express application
- `src/start.ts` — (empty, build entry point referenced in package.json scripts)
- `src/app.ts` — `App` class: configures Express, middleware stack, DB connections, route mounting

**Top-Level Modules**
```
src/
├── app.ts / server.ts / config.server.ts   — app bootstrap & config
├── routes/                                  — route definitions (6 route files)
├── controllers/                             — 6 controllers (auth, bre, cibil, experian, index, loanListView)
├── services/                                — business logic (thirdParty/, approval, bre, bureauData, customer, lead, loan, loanListView, etc.)
├── database/
│   ├── mongo/                               — MongoDB model (ThirdPartyLogs)
│   └── mysql/                              — ~55 Knex-based table models
├── bull/                                    — BullMQ producer/consumer abstractions
│   └── producer/thirdPartyLog.producer.ts  — ThirdPartyLogProducer
├── middlewares/                             — auth, error, validation, response, permission
├── config/                                  — constraint types, env vars, Redis client
├── enums/, interfaces/, types/             — shared typing
└── utils/                                  — logger (Winston), mysql (Knex), mongo (Mongoose), AES/RSA encryption, S3/SES helpers
```

**External Services**
- **MySQL** — primary DB via Knex (`src/utils/mysql.ts`); replica DB also configured
- **MongoDB** — via Mongoose (`src/utils/mongo.ts`); used for `ThirdPartyLogs`, event logs, EMI autopay logs
- **Redis** — via ioredis (`src/config/redisClient.ts`); used by BullMQ
- **BullMQ** — queue for async third-party API log ingestion (`Producer: "third-party-api-logs"`)
- **AWS S3** — document upload/download (`src/services/thirdParty/s3.service.ts`)
- **AWS SES** — email sending
- **AWS SQS** — referenced in config (`awsSQSS3Bucket`, `quickReportSQSQueueUrl`)
- **Razorpay** — payment gateway (emandate, penny-drop, orders, subscriptions)
- **Experian** — hard-pull bureau via SOAP (`src/services/thirdParty/experian.service.ts`)
- **CIBIL** — credit score API (`src/services/thirdParty/cibil.service.ts`)
- **Finbox** — bank connect / statement analysis (`src/services/thirdParty/finbox.service.ts`)
- **Decentro / SurePass / Digitap** — KYC APIs
- **External BRE APIs** (bureau decision engine, Dtree)

**Request Lifecycle**
1. Express receives request → `response.middleware` wraps `res` → `auth.middleware` validates token/customer → `validation.middleware` validates schema → Controller → Service → MySQL/MongoDB model → response

---

## ramfin_userservice.raw

**Entry Points**
- `src/server.ts` — imports `App` and `routes` array, bootstraps the Express application
- `src/start.ts` — (empty, build entry point referenced in package.json scripts)
- `src/app.ts` — `App` class: configures Express, middleware stack, DB connections, route mounting

**Top-Level Modules**
```
src/
├── app.ts / server.ts / config.server.ts   — app bootstrap & config
├── routes/                                  — route definitions (6 route files)
├── controllers/                             — 6 controllers (auth, bre, cibil, experian, index, loanListView)
├── services/                                — business logic (thirdParty/, approval, bre, bureauData, customer, lead, loan, loanListView, etc.)
├── database/
│   ├── mongo/                               — MongoDB model (ThirdPartyLogs)
│   └── mysql/                              — ~55 Knex-based table models
├── bull/                                    — BullMQ producer/consumer abstractions
│   └── producer/thirdPartyLog.producer.ts  — ThirdPartyLogProducer
├── middlewares/                             — auth, error, validation, response, permission
├── config/                                  — constraint types, env vars, Redis client
├── enums/, interfaces/, types/             — shared typing
└── utils/                                  — logger (Winston), mysql (Knex), mongo (Mongoose), AES/RSA encryption, S3/SES helpers
```

**External Services**
- **MySQL** — primary DB via Knex (`src/utils/mysql.ts`); replica DB also configured
- **MongoDB** — via Mongoose (`src/utils/mongo.ts`); used for `ThirdPartyLogs`, event logs, EMI autopay logs
- **Redis** — via ioredis (`src/config/redisClient.ts`); used by BullMQ
- **BullMQ** — queue for async third-party API log ingestion (`Producer: "third-party-api-logs"`)
- **AWS S3** — document upload/download (`src/services/thirdParty/s3.service.ts`)
- **AWS SES** — email sending
- **AWS SQS** — referenced in config (`awsSQSS3Bucket`, `quickReportSQSQueueUrl`)
- **Razorpay** — payment gateway (emandate, penny-drop, orders, subscriptions)
- **Experian** — hard-pull bureau via SOAP (`src/services/thirdParty/experian.service.ts`)
- **CIBIL** — credit score API (`src/services/thirdParty/cibil.service.ts`)
- **Finbox** — bank connect / statement analysis (`src/services/thirdParty/finbox.service.ts`)
- **Decentro / SurePass / Digitap** — KYC APIs
- **External BRE APIs** (bureau decision engine, Dtree)

**Request Lifecycle**
1. Express receives request → `response.middleware` wraps `res` → `auth.middleware` validates token/customer → `validation.middleware` validates schema → Controller → Service → MySQL/MongoDB model → response

---

## ramfincorp-backend

**Entry Points**
- `src/server.ts` — bootstraps Express app via `App` class
- `src/app.ts` — registers middleware, routes, error handling, cron jobs, DB connections

**Top-Level Modules**
```
src/
├── routes/         — Route definitions (25+ route files), registered in src/routes/index.ts
├── controllers/    — HTTP request handlers (25+ controllers)
├── services/       — Business logic layer (80+ services)
│   ├── cronJobs/   — Scheduled cron job services
│   ├── mongo/      — MongoDB-specific services
│   └── thirdParty/ — External API integrations (Razorpay, Lentra, Finbox, SurePass, Decentro, HyperVerge, Digitap, S3, Digilocker)
├── database/
│   ├── mysql/      — Knex-based models/repositories (70+ tables)
│   ├── mongo/      — Mongoose models (EventLogs, KaleyraLogs, LentraLogs, RazorpayWebhookLogs, etc.)
│   └── prisma/     — Prisma schema (MySQL User model, minimal)
├── consumers/      — SQS and Kafka consumers (missing payment, Razorpay)
├── producers/      — SQS message producers (disbursal docs, Lentra STP push, Razorpay Kafka-to-SQS)
├── middlewares/    — Auth, step checking, API key validation, logging, validation
├── queues/         — Bull/Redis queue creation
└── workers/        — Razorpay consumer worker thread
```

**External Services**
- **MySQL** (primary DB via Knex) + replica read
- **MongoDB** (Mongoose — event logs, Kaleyra logs, Lentra logs, Razorpay webhook logs)
- **Redis** (ioredis — caching, LMS flow decisions, Bull queues)
- **AWS SQS** — payment settlement, disbursal documents, Lentra STP push queues
- **AWS S3** — document/image storage
- **AWS SES** — email delivery
- **Razorpay** — payments, e-mandate, penny drop, payouts
- **PayU** — alternate payment gateway
- **Lentra LMS** — loan management system integration
- **Finbox** — bank connect, statement analysis
- **SurePass / Digitap / Decentro** — PAN/Aadhaar KYC verification
- **HyperVerge** — selfie/liveness verification
- **Firebase** — push notifications
- **Kafka** (KafkaJS) — Razorpay payment event streaming
- **Msg91 / Kaleyra / TextNation / Acquirit** — OTP/SMS delivery

**Request Lifecycle**
1. Express middleware chain (CORS, helmet, compression, rate limiting, response handler, API log save)
2. Route → validation middleware (Joi) → auth middleware (JWT/API key) → step checker middleware → controller
3. Controller calls service(s) → Knex/Mongoose DB operations → third-party API calls
4. Response via `ResponseService.serviceResponse()`

**Cron Jobs** (`CronJobService`) — auto-disbursal coverage, EMI auto-pay, UTM tracking, Razorpay webhook settlement, referral rewards, document dispatch requeue, customer expiry, Lentra STP push

---

## ramfincorp-backend.raw

**Entry Points**
- `src/server.ts` — bootstraps Express app via `App` class
- `src/app.ts` — registers middleware, routes, error handling, cron jobs, DB connections

**Top-Level Modules**
```
src/
├── routes/         — Route definitions (25+ route files), registered in src/routes/index.ts
├── controllers/    — HTTP request handlers (25+ controllers)
├── services/       — Business logic layer (80+ services)
│   ├── cronJobs/   — Scheduled cron job services
│   ├── mongo/      — MongoDB-specific services
│   └── thirdParty/ — External API integrations (Razorpay, Lentra, Finbox, SurePass, Decentro, HyperVerge, Digitap, S3, Digilocker)
├── database/
│   ├── mysql/      — Knex-based models/repositories (70+ tables)
│   ├── mongo/      — Mongoose models (EventLogs, KaleyraLogs, LentraLogs, RazorpayWebhookLogs, etc.)
│   └── prisma/     — Prisma schema (MySQL User model, minimal)
├── consumers/      — SQS and Kafka consumers (missing payment, Razorpay)
├── producers/      — SQS message producers (disbursal docs, Lentra STP push, Razorpay Kafka-to-SQS)
├── middlewares/    — Auth, step checking, API key validation, logging, validation
├── queues/         — Bull/Redis queue creation
└── workers/        — Razorpay consumer worker thread
```

**External Services**
- **MySQL** (primary DB via Knex) + replica read
- **MongoDB** (Mongoose — event logs, Kaleyra logs, Lentra logs, Razorpay webhook logs)
- **Redis** (ioredis — caching, LMS flow decisions, Bull queues)
- **AWS SQS** — payment settlement, disbursal documents, Lentra STP push queues
- **AWS S3** — document/image storage
- **AWS SES** — email delivery
- **Razorpay** — payments, e-mandate, penny drop, payouts
- **PayU** — alternate payment gateway
- **Lentra LMS** — loan management system integration
- **Finbox** — bank connect, statement analysis
- **SurePass / Digitap / Decentro** — PAN/Aadhaar KYC verification
- **HyperVerge** — selfie/liveness verification
- **Firebase** — push notifications
- **Kafka** (KafkaJS) — Razorpay payment event streaming
- **Msg91 / Kaleyra / TextNation / Acquirit** — OTP/SMS delivery

**Request Lifecycle**
1. Express middleware chain (CORS, helmet, compression, rate limiting, response handler, API log save)
2. Route → validation middleware (Joi) → auth middleware (JWT/API key) → step checker middleware → controller
3. Controller calls service(s) → Knex/Mongoose DB operations → third-party API calls
4. Response via `ResponseService.serviceResponse()`

**Cron Jobs** (`CronJobService`) — auto-disbursal coverage, EMI auto-pay, UTM tracking, Razorpay webhook settlement, referral rewards, document dispatch requeue, customer expiry, Lentra STP push

---

## ramfincorp-notification

**Entry Point**
- `src/server.ts` → instantiates `App` with routes from `src/routes/index.ts`, starts HTTP server

**Top-level modules**
```
src/
├── app.ts                    — Express app setup, middleware registration, Swagger, BullMQ init, cron start
├── server.ts                 — Boot entry point
├── config.server.ts          — Config loader (env vars + defaults)
├── routes/                   — Route definitions (IndexRoute, LogsRoute, NotificationRoute)
├── controllers/              — Request handlers (index, logs, notification)
├── services/                 — Business logic (notification, logs, firebase, kaleyra, mail, mobile_token, etc.)
├── bull/                     — BullMQ consumers (ThirdPartyLogConsumer)
├── queues/                   — Redis connection + queue factory (bull legacy + bullmq)
├── database/
│   ├── mongo/model/          — Mongoose models (logs, users, etc.)
│   ├── mongo/repository/     — Mongo repos (CustomerAsset, User)
│   ├── mysql/                — Knex-based model classes (50+ tables)
│   └── prisma/schema.prisma  — Prisma schema (MySQL, User model only)
├── middlewares/              — Express middlewares (auth, error, validation, pagination, etc.)
├── validations/              — Joi schemas
├── helpers/                  — CommonHelper, date helpers, EMI helpers
└── utils/                    — Logger (Winston), MySQL (Knex), Mongo (Mongoose), Redis (ioredis), etc.
```

**External services / dependencies**
- **MySQL** — primary relational store via Knex (`src/utils/mysql.ts`)
- **MongoDB** — logging & asset data via Mongoose (`src/utils/mongo.ts`)
- **Redis** — BullMQ queues & legacy Bull queues (`src/config/redis.ts`, `src/queues/`)
- **AWS S3** — document upload via `S3Service`
- **AWS SES** — email delivery via `S3Service.sendEmail`
- **Razorpay** — payment, mandate, subscription APIs (via axios in services)
- **Firebase FCM** — push notifications (`src/services/firebase.service.ts`)
- **Kaleyra / TextNation / Acquirit / MSG91** — SMS providers
- **WhatsApp API** — configured via `config.whatsappInteract`
- **Sendinblue/Bravo** — email (`src/services/common.ts`)

**Core request lifecycle**
`server.ts` → `App` → Express middlewares (helmet, cors, morgan, validation, pagination) → Route → Controller → Service → DB model (MySQL/Mongo) → Response middleware

**BullMQ job lifecycle**
Producer queues `IThirdPartyApiLogs` job → Redis → `ThirdPartyLogConsumer.processJob()` → saves to MongoDB `ThirdPartyApiLogs`

---

## ramfincorp-notification.raw

**Entry Point**
- `src/server.ts` → instantiates `App` with routes from `src/routes/index.ts`, starts HTTP server

**Top-level modules**
```
src/
├── app.ts                    — Express app setup, middleware registration, Swagger, BullMQ init, cron start
├── server.ts                 — Boot entry point
├── config.server.ts          — Config loader (env vars + defaults)
├── routes/                   — Route definitions (IndexRoute, LogsRoute, NotificationRoute)
├── controllers/              — Request handlers (index, logs, notification)
├── services/                 — Business logic (notification, logs, firebase, kaleyra, mail, mobile_token, etc.)
├── bull/                     — BullMQ consumers (ThirdPartyLogConsumer)
├── queues/                   — Redis connection + queue factory (bull legacy + bullmq)
├── database/
│   ├── mongo/model/          — Mongoose models (logs, users, etc.)
│   ├── mongo/repository/     — Mongo repos (CustomerAsset, User)
│   ├── mysql/                — Knex-based model classes (50+ tables)
│   └── prisma/schema.prisma  — Prisma schema (MySQL, User model only)
├── middlewares/              — Express middlewares (auth, error, validation, pagination, etc.)
├── validations/              — Joi schemas
├── helpers/                  — CommonHelper, date helpers, EMI helpers
└── utils/                    — Logger (Winston), MySQL (Knex), Mongo (Mongoose), Redis (ioredis), etc.
```

**External services / dependencies**
- **MySQL** — primary relational store via Knex (`src/utils/mysql.ts`)
- **MongoDB** — logging & asset data via Mongoose (`src/utils/mongo.ts`)
- **Redis** — BullMQ queues & legacy Bull queues (`src/config/redis.ts`, `src/queues/`)
- **AWS S3** — document upload via `S3Service`
- **AWS SES** — email delivery via `S3Service.sendEmail`
- **Razorpay** — payment, mandate, subscription APIs (via axios in services)
- **Firebase FCM** — push notifications (`src/services/firebase.service.ts`)
- **Kaleyra / TextNation / Acquirit / MSG91** — SMS providers
- **WhatsApp API** — configured via `config.whatsappInteract`
- **Sendinblue/Bravo** — email (`src/services/common.ts`)

**Core request lifecycle**
`server.ts` → `App` → Express middlewares (helmet, cors, morgan, validation, pagination) → Route → Controller → Service → DB model (MySQL/Mongo) → Response middleware

**BullMQ job lifecycle**
Producer queues `IThirdPartyApiLogs` job → Redis → `ThirdPartyLogConsumer.processJob()` → saves to MongoDB `ThirdPartyApiLogs`

---

## stored-procedure-RamFin

This repository is a pure collection of MySQL stored procedures for RamFin's loan management platform. There is no application server, ORM, or service layer — all logic is expressed as `CREATE PROCEDURE` DDL statements.

**Storage Backend: Single MySQL database (`ramfin`)**
- Cross-database reference to `dsa` schema (DSA user management)

**Procedure Categories:**

- **Lead & Onboarding Reports**
  - `All_leads`, `get_lead_data`, `leads_not_completed_status_report_data`, `NotCompletedReport`, `event_funnel_report`, `event_funnel_reports`, `event_funnel_report_generate`, `user_funnel`, `event_data`
  - `api_log_data_with_error`, `get_journey_logs` (API monitoring)

- **Disbursal Reports**
  - `get_disbursal_data`, `get_disbursal_data_account`, `get_disbursal_data_account_ava`, `get_disbursal_data_quick_report`, `disbursalAmount_asondate`
  - `sp_disbursal_attribution_report`

- **Collection Reports**
  - `get_collection_data`, `get_collection_data_report_dashboard`, `get_collection_data_report_dashboard_created_at`, `get_collection_data_report_dashboard_optimized`
  - `collection_summary`, `collection_summary_aa`, `collection_summary_dd`, `collection_summary_nnew`, `collection_summarya`
  - `CollectionCityWiseProcedure`, `CollectionCreditmanagerWiseProcedure`, `CollectionSanctionalmanagerWiseProcedure`
  - `emi_collection_summary`, `collection_emi_data`, `emi_loan_collection_detail`
  - `pending_collection_summary_report`, `update_collection_calculations`

- **Loan Book / AUM**
  - `get_loan_book_data`, `get_loan_book_data_aum`, `get_loan_book_data_withemi`, `get_loan_book_data_withemi_specific`
  - `get_loan_book_data_withemi_static`, `get_loan_book_data_withemi_static_90`, `get_loan_book_data_withemi_static90`
  - `GetLoanbookSummaryRange`, `fy_monthly_summary`

- **Pending/Overdue Reports**
  - `payday_pending_report`, `payday_pending_report_phone`, `payday_pending_report_optimized`
  - `payday_pending_emi_report`, `payday_pending_emi_report_phone`, `datewise_payday_pending`, `DateWiseEMI`

- **DSA/Partner Reports**
  - `dsa_partner_data_as_disbursal`, `dsa_partner_data_as_disbursal_billing`, `dsa_partner_data_as_leads`, `dsa_partner_data_as_leads_new`, `dsa_partner_data_list`
  - `dsa_userwise_report`, `dsa_userwise_report_new`, `dsa_userwise_report_opt`
  - `agent_dsa_report`, `sp_lead_status_report`, `sp_lead_status_count_report`

- **Credit/Rejection/DPD Reports**
  - `CreditReportNewCasesProcedure`, `CreditReportRepeatCasesProcedure`, `rejection`, `repeat_dpd_report`, `repeat_dpd_reports`
  - `approved_process_transition`, `get_approval_process_counts_data`

- **Collection Status Procedures (Account-level)**
  - `ActualPaymentProcedure`, `ClosedAccountsProcedure`, `SettledAccountsProcedure`, `PartPayment`, `PendingAccountsProcedure`, `TotalLoanRepayment`, `TotalCasesProcedure`

- **Utility/Admin**
  - `grant_loanbook_access`, `GetCountsFromAllTables`, `update_all_timestamp_columns_with_logs`, `log_shifting_api_req_res_log`
  - `not_active_customer`, `mom_repeat_report`, `salaried_vs_self_employed_report`, `cibil_data_dump`, `settlement_data`

**External schema dependency:** `dsa.users`, `dsa.commission_slab`, `dsa.profile` (cross-database joins)

---

## stored-procedure-RamFin.raw

This repository is a pure collection of MySQL stored procedures for RamFin's loan management platform. There is no application server, ORM, or service layer — all logic is expressed as `CREATE PROCEDURE` DDL statements.

**Storage Backend: Single MySQL database (`ramfin`)**
- Cross-database reference to `dsa` schema (DSA user management)

**Procedure Categories:**

- **Lead & Onboarding Reports**
  - `All_leads`, `get_lead_data`, `leads_not_completed_status_report_data`, `NotCompletedReport`, `event_funnel_report`, `event_funnel_reports`, `event_funnel_report_generate`, `user_funnel`, `event_data`
  - `api_log_data_with_error`, `get_journey_logs` (API monitoring)

- **Disbursal Reports**
  - `get_disbursal_data`, `get_disbursal_data_account`, `get_disbursal_data_account_ava`, `get_disbursal_data_quick_report`, `disbursalAmount_asondate`
  - `sp_disbursal_attribution_report`

- **Collection Reports**
  - `get_collection_data`, `get_collection_data_report_dashboard`, `get_collection_data_report_dashboard_created_at`, `get_collection_data_report_dashboard_optimized`
  - `collection_summary`, `collection_summary_aa`, `collection_summary_dd`, `collection_summary_nnew`, `collection_summarya`
  - `CollectionCityWiseProcedure`, `CollectionCreditmanagerWiseProcedure`, `CollectionSanctionalmanagerWiseProcedure`
  - `emi_collection_summary`, `collection_emi_data`, `emi_loan_collection_detail`
  - `pending_collection_summary_report`, `update_collection_calculations`

- **Loan Book / AUM**
  - `get_loan_book_data`, `get_loan_book_data_aum`, `get_loan_book_data_withemi`, `get_loan_book_data_withemi_specific`
  - `get_loan_book_data_withemi_static`, `get_loan_book_data_withemi_static_90`, `get_loan_book_data_withemi_static90`
  - `GetLoanbookSummaryRange`, `fy_monthly_summary`

- **Pending/Overdue Reports**
  - `payday_pending_report`, `payday_pending_report_phone`, `payday_pending_report_optimized`
  - `payday_pending_emi_report`, `payday_pending_emi_report_phone`, `datewise_payday_pending`, `DateWiseEMI`

- **DSA/Partner Reports**
  - `dsa_partner_data_as_disbursal`, `dsa_partner_data_as_disbursal_billing`, `dsa_partner_data_as_leads`, `dsa_partner_data_as_leads_new`, `dsa_partner_data_list`
  - `dsa_userwise_report`, `dsa_userwise_report_new`, `dsa_userwise_report_opt`
  - `agent_dsa_report`, `sp_lead_status_report`, `sp_lead_status_count_report`

- **Credit/Rejection/DPD Reports**
  - `CreditReportNewCasesProcedure`, `CreditReportRepeatCasesProcedure`, `rejection`, `repeat_dpd_report`, `repeat_dpd_reports`
  - `approved_process_transition`, `get_approval_process_counts_data`

- **Collection Status Procedures (Account-level)**
  - `ActualPaymentProcedure`, `ClosedAccountsProcedure`, `SettledAccountsProcedure`, `PartPayment`, `PendingAccountsProcedure`, `TotalLoanRepayment`, `TotalCasesProcedure`

- **Utility/Admin**
  - `grant_loanbook_access`, `GetCountsFromAllTables`, `update_all_timestamp_columns_with_logs`, `log_shifting_api_req_res_log`
  - `not_active_customer`, `mom_repeat_report`, `salaried_vs_self_employed_report`, `cibil_data_dump`, `settlement_data`

**External schema dependency:** `dsa.users`, `dsa.commission_slab`, `dsa.profile` (cross-database joins)

---

