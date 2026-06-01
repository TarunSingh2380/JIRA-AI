## ARCHITECTURE

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

## ROUTES

**Auth (`src/routes/auth.route.ts`)**
`POST /auth/signup/otp  ->  AuthController.signupOTP  (src/controllers/auth.controller.ts)  — Send OTP for signup`
`POST /auth/signup/verify  ->  AuthController.signupVerifyOTP  (src/controllers/auth.controller.ts)  — Verify OTP and complete signup`
`POST /auth/signin/otp  ->  AuthController.signInOTP  (src/controllers/auth.controller.ts)  — Send OTP for sign-in`
`POST /auth/signin  ->  AuthController.signIn  (src/controllers/auth.controller.ts)  — Sign in with email`
`POST /auth/signout  ->  AuthController.signOut  (src/controllers/auth.controller.ts)  — Sign out user`

**Index (`src/routes/index.route.ts`)**
`GET /  ->  IndexController (src/controllers/index.controller.ts)  — Health check / root`

**User (`src/routes/user.route.ts`)**
`GET /users  ->  UsersController.getDsaUsers  (src/controllers/users.controller.ts)  — List DSA users`
`GET /users/dropdown  ->  UsersController.getDsaDropdownUsers  (src/controllers/users.controller.ts)  — Get users for dropdown`
`GET /users/search  ->  UsersController.searchUsersByName  (src/controllers/users.controller.ts)  — Search users by name`
`GET /users/:id  ->  UsersController.getUserById  (src/controllers/users.controller.ts)  — Get user by ID`
`POST /users  ->  UsersController.createUser  (src/controllers/users.controller.ts)  — Create a new user`
`PUT /users/:id  ->  UsersController.updateUser  (src/controllers/users.controller.ts)  — Update user`
`POST /users/activate  ->  UsersController.activateUser  (src/controllers/users.controller.ts)  — Activate a user`
`POST /users/profile  ->  UsersController.createUserProfile  (src/controllers/users.controller.ts)  — Create/update user profile`
`POST /users/business  ->  UsersController.addBusiness  (src/controllers/users.controller.ts)  — Add business details`
`POST /users/bank  ->  UsersController.addBank  (src/controllers/users.controller.ts)  — Add bank details`
`POST /users/commission  ->  UsersController.updateCommissionData  (src/controllers/users.controller.ts)  — Update commission slabs`
`GET /users/utm-links  ->  UsersController.getUtmLinks  (src/controllers/users.controller.ts)  — Get UTM links for user`
`POST /users/utm-links  ->  UsersController.generateUtmLinkV2  (src/controllers/users.controller.ts)  — Generate UTM link`
`GET /users/qrcode  ->  UsersController.getQrcode  (src/controllers/users.controller.ts)  — Get QR code for UTM`

**DSA (`src/routes/dsa.route.ts`)**
`POST /dsa/leads/upload  ->  DsaController.uploadLeads  (src/controllers/dsa.controller.ts)  — Upload lead file`
`GET /dsa/leads/upload-list  ->  DsaController.getUploadList  (src/controllers/dsa.controller.ts)  — Get lead upload list`
`GET /dsa/leads/upload-list/download  ->  DsaController.getUploadListDownload  (src/controllers/dsa.controller.ts)  — Download upload list`
`GET /dsa/leads/status  ->  DsaController.getLeadFileStatus  (src/controllers/dsa.controller.ts)  — Get lead file processing status`
`POST /dsa/leads/validate  ->  DsaController.validateAndSaveLeads  (src/controllers/dsa.controller.ts)  — Validate and save leads from file`
`POST /dsa/leads/create  ->  DsaController.createLeads  (src/controllers/dsa.controller.ts)  — Create leads via API gateway`
`GET /dsa/report  ->  DsaController.getDsaReport  (src/controllers/dsa.controller.ts)  — Get DSA summary report`
`GET /dsa/report/data  ->  DsaController.getDsaReportData  (src/controllers/dsa.controller.ts)  — Get DSA report raw data`
`GET /dsa/detail  ->  DsaController.getDsaDetail  (src/controllers/dsa.controller.ts)  — Get DSA detail`
`GET /dsa/leads/list  ->  DsaController.getDsaLeadList  (src/controllers/dsa.controller.ts)  — Get paginated lead list`
`GET /dsa/leads/list/download  ->  DsaController.getDsaLeadListDownload  (src/controllers/dsa.controller.ts)  — Download lead list as Excel`
`POST /dsa/leads/list/queue  ->  DsaController.enqueueDsaLeadListReport  (src/controllers/dsa.controller.ts)  — Enqueue lead list report generation`
`GET /dsa/merchant/list  ->  DsaController.getDSAMerchantList  (src/controllers/dsa.controller.ts)  — Get merchant list`
`POST /dsa/commission/invoice  ->  DsaController.uploadCommissionInvoice  (src/controllers/dsa.controller.ts)  — Upload commission invoice`
`POST /dsa/commission/payment  ->  DsaController.createPayment  (src/controllers/dsa.controller.ts)  — Create commission payment`
`GET /dsa/commission/reports  ->  DsaController.getCommissionReports  (src/controllers/dsa.controller.ts)  — Get commission reports`
`PUT /dsa/commission/status  ->  DsaController.updateCommissionStatus  (src/controllers/dsa.controller.ts)  — Update commission status`
`PUT /dsa/commission/payment/status  ->  DsaController.updatePaymentStatus  (src/controllers/dsa.controller.ts)  — Update payment status`
`POST /dsa/leads/download/request  ->  DsaController.requestLeadDownload  (src/controllers/dsa.controller.ts)  — Request async lead download`
`GET /dsa/leads/download/history  ->  DsaController.getLeadDownloadHistory  (src/controllers/dsa.controller.ts)  — Get lead download history`
`GET /dsa/leads/download/url  ->  DsaController.getLeadDownloadPresignedUrl  (src/controllers/dsa.controller.ts)  — Get presigned URL for download`
`GET /dsa/document/download  ->  DsaController.downloadDocument  (src/controllers/dsa.controller.ts)  — Download a document by URL`

**Media (`src/routes/media.route.ts`)**
`POST /media/upload  ->  MediaController (src/controllers/media.controller.ts)  — Initiate/manage S3 media upload (presigned/multipart)`

**SQS Consumer (`src/consumer/router.ts`)**
`SQS message [dsaUserwiseReport event]  ->  processDsaUserwiseReport  (src/consumer/processors/dsaUserwiseReport.processor.ts)  — Process queued DSA userwise lead report`

**Cron Jobs (`src/services/cronJobs/cronJobs.service.ts`)**
`CRON monthly  ->  CronJobService.commissionGeneration  (src/services/cronJobs/cronJobs.service.ts)  — Generate monthly commission reports`

## DATA_MODELS

**MySQL — Primary DSA Database (AppDataSource / TypeORM)**

`User  (src/database/entity/user.entity.ts)  — fields: id (PrimaryColumn), name, email, mobile, role (USER_ROLES), status (USER_STATUS), verificationStatus (VERIFICATION_STATUS), utmLink, internalUserId, createdAt, updatedAt  — relationships: OneToOne Profile, OneToMany LeadFiles, OneToMany UserLeads`

`Profile  (src/database/entity/profile.entity.ts)  — fields: id, userId, firstName, lastName, aadhaarNumber, panNumber, utmCode, createdAt, updatedAt  — relationships: OneToOne User, OneToMany BankDetails, OneToMany CommissionSlab, OneToOne BusinessDetails`

`BankDetails  (src/database/entity/bankDetails.entity.ts)  — fields: id, profileId, accountNumber, ifscCode, bankName, accountHolderName, active, createdAt, updatedAt  — relationships: ManyToOne Profile`

`BusinessDetails  (src/database/entity/businessDetails.entity.ts)  — fields: id, profileId, businessType (BusinessType), businessName, gstNumber, createdAt, updatedAt  — relationships: ManyToOne Profile`

`CommissionSlab  (src/database/entity/commissionsSlab.entity.ts)  — fields: id, profileId, type ('disbursal'|'leads'), start, end, commissionValue, createdAt, updatedAt  — relationships: ManyToOne Profile`

`CommissionReport  (src/database/entity/commissionReport.entity.ts)  — fields: id, userId, status (CommissionStatus), disbursedAmount, commission, gst, gstAmount, tdsAmount, totalCommission, invoiceUrl, remarks, createdAt, updatedAt  — relationships: ManyToOne User, OneToOne CommissionPayment`

`CommissionPayment  (src/database/entity/commissionPayment.entity.ts)  — fields: id, reportId, status (PaymentStatus), referenceNumber, createdAt, updatedAt  — relationships: ManyToOne CommissionReport`

`LeadFiles  (src/database/entity/leadFiles.entity.ts)  — fields: id, userId, fileName, status (leadFileStatus), errorMsg, createdAt, updatedAt  — relationships: ManyToOne User, OneToMany UserLeads`

`UserLeads  (src/database/entity/userLeads.entity.ts)  — fields: id, leadFileId, userId, status (LeadStatus), name, mobile, loanAmount, email, employeeType, dob, utmCode, createdAt, updatedAt  — relationships: ManyToOne User, ManyToOne LeadFiles`

`Otp  (src/database/entity/otp.entity.ts)  — fields: id, userId, otp, requestId, expiresAt, createdAt, updatedAt  — relationships: ManyToOne User`

`S3MediaMetadata  (src/database/entity/s3MediaMetadata.entity.ts)  — fields: id, key, bucket, contentType, createdAt, updatedAt`

`LeadDownloadRecord  (src/database/entity/leadDownloadRecord.entity.ts)  — fields: id, userId, startDate, endDate, leadFilter, fileName, leadStatus, status (LeadDownloadStatus), createdAt, updatedAt  — relationships: ManyToOne User`

`UserUtmLink  (src/database/entity/userUtmLink.entity.ts)  — fields: id, userId, utmSource, utmLink, platform (Platform), utmCampaign, utmMedium, createdAt`

**MySQL — Ramfin Database (AppDataSourceRamfin / TypeORM)**

`RamfinUser  (src/database/entity/ramfinUser.entity.ts)  — fields: id, phoneNo, email, username, referralCode, utmSource, role, name, createdAt, updatedAt`

`LeadEntity  (src/database/entity/leads.entity.ts)  — fields: id, status (LeadStatus enum: NEW/IN_PROGRESS/APPROVED/REJECTED/CLOSED), createdAt`

`UserAttribution  (src/database/entity/userAttribution.entity.ts)  — fields: id, createdAt`

`CredentialEntity  (src/database/entity/credential.entity.ts)  — fields: id, createdAt, updatedAt`

`SwitchThirdPartApiEntity  (src/database/entity/switchThirdPartyApi.Entity.ts)  — fields: id`

**Redis (ioredis — src/redis/index.ts)**

`Cache entries  (src/redis/cache.service.ts)  — key-value store with optional TTL (default 7 days); used for: active SMS/notification vendor credentials, UTM links, general getOrSetCache patterns`