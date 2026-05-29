## ARCHITECTURE

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

## ROUTES

### Login
```
POST /login/login                    -> LoginController (login.route.ts) — CRM user login
POST /login/verify-otp               -> LoginController (login.route.ts) — Verify OTP
POST /login/forgot-password          -> LoginController (login.route.ts) — Forgot password
POST /login/update-password          -> LoginController (login.route.ts) — Update password
POST /login/validate-otp             -> LoginController (login.route.ts) — Validate OTP
POST /login/login-with-mac           -> LoginController (login.route.ts) — Login with MAC address
POST /login/login-validation         -> LoginController (login.route.ts) — Login validation
POST /login/assign-mac-address       -> LoginController (login.route.ts) — Assign MAC address
```

### Lead
```
POST   /lead/lead-list               -> LEADController (lead.route.ts) — Paginated lead listing
POST   /lead/credit-list             -> LEADController (lead.route.ts) — Credit list
POST   /lead/sanction-list           -> LEADController (lead.route.ts) — Sanction list
POST   /lead/unprocessed-list        -> LEADController (lead.route.ts) — Unprocessed leads
POST   /lead/again-no-loan-list      -> LEADController (lead.route.ts) — Again-no-loan list
POST   /lead/no-eligible-list        -> LEADController (lead.route.ts) — Not eligible leads
POST   /lead/change-lead-status      -> LEADController (lead.route.ts) — Change lead status
POST   /lead/add-collection          -> LEADController (lead.route.ts) — Add collection (Payday)
POST   /lead/add-emi-collection      -> LEADController (lead.route.ts) — Add EMI collection
POST   /lead/collection-details      -> LEADController (lead.route.ts) — Collection details for lead
POST   /lead/collection-follow-up    -> LEADController (lead.route.ts) — Collection follow-up
POST   /lead/create-address          -> LEADController (lead.route.ts) — Create address
POST   /lead/create-employment       -> LEADController (lead.route.ts) — Create employment details
POST   /lead/reference-details       -> LEADController (lead.route.ts) — Add reference details
POST   /lead/check-pincode           -> LEADController (lead.route.ts) — Check pincode
POST   /lead/modify-loan             -> LEADController (lead.route.ts) — Modify loan details
POST   /lead/modify-emi-loan         -> LEADController (lead.route.ts) — Modify EMI loan
POST   /lead/get-repayment-date      -> LEADController (lead.route.ts) — Get repayment date list
POST   /lead/update-repayment-date   -> LEADController (lead.route.ts) — Update repayment date
POST   /lead/name-mismatch           -> LEADController (lead.route.ts) — Get name mismatch data
POST   /lead/name-mismatch-action    -> LEADController (lead.route.ts) — Accept/reject name mismatch
POST   /lead/no-dues                 -> LEADController (lead.route.ts) — Generate no-dues certificate
POST   /lead/get-loan-details        -> LEADController (lead.route.ts) — Get loan details
POST   /lead/get-emi-loan-details    -> LEADController (lead.route.ts) — Get EMI loan details
POST   /lead/get-soa                 -> LEADController (lead.route.ts) — Get statement of account
POST   /lead/generate-soa            -> LEADController (lead.route.ts) — Generate SOA by leadId
POST   /lead/credit-detail           -> LEADController (lead.route.ts) — Credit detail
POST   /lead/allocate-to-me          -> LEADController (lead.route.ts) — Allocate lead to me
POST   /lead/check-penny-drop        -> LEADController (lead.route.ts) — Trigger penny drop check
POST   /lead/lead-refund-update      -> LEADController (lead.route.ts) — Update lead refund
POST   /lead/collection-mode-update  -> LEADController (lead.route.ts) — Update collection mode
POST   /lead/download-collection-csv -> LEADController (lead.route.ts) — Download collection CSV
POST   /lead/again-no-loan-follow-up -> LEADController (lead.route.ts) — Add again-no-loan follow-up
POST   /lead/get-again-no-loan-follow-up -> LEADController (lead.route.ts) — Get again-no-loan follow-up
POST   /lead/blacklist-customer-add  -> LEADController (lead.route.ts) — Add customer to blacklist
POST   /lead/sync-whitelist-ramfin   -> LEADController (lead.route.ts) — Sync whitelist
POST   /lead/payment-mode-manager    -> LEADController (lead.route.ts) — Payment mode manager
POST   /lead/virtual-account         -> LEADController (lead.route.ts) — Virtual account tab
POST   /lead/generate-emandate       -> LEADController (lead.route.ts) — Generate emandate
POST   /lead/disable-emandate        -> LEADController (lead.route.ts) — Disable emandate
POST   /lead/charge-emandate         -> LEADController (lead.route.ts) — Charge emandate
POST   /lead/bank-account-details    -> LEADController (lead.route.ts) — Bank account details
POST   /lead/disbursal-by-lead       -> LEADController (lead.route.ts) — Disbursal letter
POST   /lead/noDuesPdf               -> LEADController (lead.route.ts) — No-dues PDF
POST   /lead/selfie-liveness         -> LEADController (lead.route.ts) — Selfie liveness data
POST   /lead/selfie-liveness-image   -> LEADController (lead.route.ts) — Selfie liveness image
POST   /lead/update-selfie-liveness  -> LEADController (lead.route.ts) — Update selfie liveness
POST   /lead/loan-modification-list  -> LEADController (lead.route.ts) — Loan modification list
POST   /lead/loan-modification-report-> LEADController (lead.route.ts) — Loan modification report
POST   /lead/send-settlement-email   -> LEADController (lead.route.ts) — Send settlement email
POST   /lead/settlement-data         -> LEADController (lead.route.ts) — Settlement data
POST   /lead/trigger-loan-write-off  -> LEADController (lead.route.ts) — Trigger loan write-off by date
POST   /lead/decrypt-mobile          -> LEADController (lead.route.ts) — Decrypt mobile number
POST   /lead/list-decrypt-mobile     -> LEADController (lead.route.ts) — List decrypted mobiles
GET    /lead/crm-timeline/:leadID    -> LEADController (lead.route.ts) — CRM timeline
GET    /lead/profile/:leadID         -> LEADController (lead.route.ts) — Get lead profile
GET    /lead/assigned-lead           -> LEADController (lead.route.ts) — Get assigned lead ID
POST   /lead/callback-request        -> LEADController (lead.route.ts) — Callback request list
POST   /lead/credit-manager-names    -> LEADController (lead.route.ts) — Credit manager name/IDs
POST   /lead/leads-api-json-view     -> LEADController (lead.route.ts) — Leads API JSON view
```

### CRM
```
POST /crm/update-lead                -> CRMController (crm.route.ts) — Update lead
POST /crm/emi-calculator             -> CRMController (crm.route.ts) — EMI calculator
POST /crm/credit-details             -> CRMController (crm.route.ts) — Save credit details
POST /crm/get-amount-to-disbursed    -> CRMController (crm.route.ts) — Get disbursable amount
POST /crm/generate-emi               -> CRMController (crm.route.ts) — Generate EMI to DB
POST /crm/update-payment             -> CRMController (crm.route.ts) — Update payment
POST /crm/apply-penalty              -> CRMController (crm.route.ts) — Apply penalty
POST /crm/get-emis                   -> CRMController (crm.route.ts) — Get EMIs
POST /crm/get-docs-requirements      -> CRMController (crm.route.ts) — Get docs requirements
POST /crm/get-emi-loan-details       -> CRMController (crm.route.ts) — Get EMI loan details
POST /crm/upload-bulk-mandate        -> CRMController (crm.route.ts) — Upload bulk mandate file
POST /crm/get-bulk-mandate-data      -> CRMController (crm.route.ts) — Get bulk mandate data
POST /crm/get-url-for-bulk-mandate   -> CRMController (crm.route.ts) — Get URL for bulk mandate
POST /crm/upload-not-required-file   -> CRMController (crm.route.ts) — Upload not-required file
POST /crm/payday-to-emi-conversion   -> CRMController (crm.route.ts) — Payday to EMI conversion
POST /crm/loan-details-by-pan        -> CRMController (crm.route.ts) — Loan details by PAN
POST /crm/loan-agreement-letter      -> CRMController (crm.route.ts) — Loan agreement letter
```

### Collection
```
POST /collection/pending-payday           -> CollectionController (collection.route.ts) — Pending Payday collection
POST /collection/download-pending-payday  -> CollectionController (collection.route.ts) — Download Payday collection Excel
POST /collection/pending-emi              -> CollectionController (collection.route.ts) — Pending EMI collection
POST /collection/download-pending-emi     -> CollectionController (collection.route.ts) — Download EMI collection Excel
POST /collection/allocate-multiple        -> CollectionController (collection.route.ts) — Allocate multiple leads
POST /collection/collection-report-closed -> CollectionController (collection.route.ts) — Closed collection report
POST /collection/download-closed          -> CollectionController (collection.route.ts) — Download closed collection Excel
POST /collection/part-payment             -> CollectionController (collection.route.ts) — Part payment collection
POST /collection/download-part-payment    -> CollectionController (collection.route.ts) — Download part payment Excel
POST /collection/settlement               -> CollectionController (collection.route.ts) — Settlement collection
POST /collection/download-settlement      -> CollectionController (collection.route.ts) — Download settlement Excel
POST /collection/waive-off-details        -> CollectionController (collection.route.ts) — Waive-off loan details
POST /collection/add-waive-off            -> CollectionController (collection.route.ts) — Add waive-off
POST /collection/collection-manager       -> CollectionController (collection.route.ts) — Collection manager list
POST /collection/collection-manager-action -> CollectionController (collection.route.ts) — Approve/reject collection
POST /collection/collection-manager-action-multiple -> CollectionController (collection.route.ts) — Bulk approve/reject
POST /collection/change-payment-mode      -> CollectionController (collection.route.ts) — Change payment mode
POST /collection/payment-settlement-again -> CollectionController (collection.route.ts) — Settlement recalculate
GET  /collection/dnd-list                 -> CustomerController (collection.route.ts) — DND customer list
POST /collection/delete-dnd               -> CustomerController (collection.route.ts) — Delete DND
POST /collection/add-dnd                  -> CustomerController (collection.route.ts) — Add DND
POST /collection/edit-dnd                 -> CustomerController (collection.route.ts) — Edit DND
POST /collection/download-dnd             -> CustomerController (collection.route.ts) — Download DND Excel
```

### Customer
```
POST /customer/global-search             -> CustomerController (customer.routes.ts) — Global search
POST /customer/get-customer-list         -> CustomerController (customer.routes.ts) — Customer list
POST /customer/update-customer           -> CustomerController (customer.routes.ts) — Update customer details
POST /customer/set-source-partner        -> CustomerController (customer.routes.ts) — Set source partner
POST /customer/edit-source-partner       -> CustomerController (customer.routes.ts) — Edit source partner
POST /customer/get-source-partner        -> CustomerController (customer.routes.ts) — Get source partners
POST /customer/feedback-list             -> CustomerController (customer.routes.ts) — Feedback list
POST /customer/pan-verification          -> CustomerController (customer.routes.ts) — PAN verification
POST /customer/aadhar-otp                -> CustomerController (customer.routes.ts) — Aadhaar OTP
POST /customer/verify-aadhar-otp         -> CustomerController (customer.routes.ts) — Verify Aadhaar OTP
POST /customer/ckyc                      -> CustomerController (customer.routes.ts) — CKYC fetch
POST /customer/blacklist-pan             -> CustomerController (customer.routes.ts) — Blacklist PAN (CSV upload)
POST /customer/upload-blacklist-pan      -> CustomerController (customer.routes.ts) — Upload blacklist PAN CSV
GET  /customer/api-log/:customerID       -> CustomerController (customer.routes.ts) — Get API log
```

### Disbursal
```
POST /disbursal/bank-update              -> DisbursalController (disbursal.route.ts) — Bank update/disbursal list
POST /disbursal/export-manual-disbursal  -> DisbursalController (disbursal.route.ts) — Export manual disbursal
POST /disbursal/import-manual-disbursal  -> DisbursalController (disbursal.route.ts) — Import manual disbursal
POST /disbursal/allocate                 -> DisbursalController (disbursal.route.ts) — Allocate disbursal leads
POST /disbursal/initiate                 -> DisbursalController (disbursal.route.ts) — Initiate disbursal
POST /disbursal/bank-update-reject-failed -> DisbursalController (disbursal.route.ts) — Mark bank update failed
POST /disbursal/re-initiate              -> DisbursalController (disbursal.route.ts) — Re-initiate disbursal
```

### Report
```
POST /report/customer-feedback           -> ReportController (report.route.ts) — Customer feedback report
POST /report/disbursal-data              -> ReportController (report.route.ts) — Disbursal data report
POST /report/download-disbursal-data     -> ReportController (report.route.ts) — Download disbursal Excel
POST /report/collection-data            -> ReportController (report.route.ts) — Collection data report
POST /report/download-collection-data   -> ReportController (report.route.ts) — Download collection Excel
POST /report/date-wise-pending          -> ReportController (report.route.ts) — Date-wise pending payment
POST /report/date-wise-lead             -> ReportController (report.route.ts) — Date-wise lead report
POST /report/download-date-wise-lead    -> ReportController (report.route.ts) — Download date-wise lead Excel
POST /report/date-wise-collection       -> ReportController (report.route.ts) — Date-wise collection report
POST /report/download-date-wise-collection -> ReportController (report.route.ts) — Download date-wise collection Excel
POST /report/app-issue                  -> ReportController (report.route.ts) — App issue report
POST /report/refund                     -> ReportController (report.route.ts) — Refund report
POST /report/utm-sources                -> ReportController (report.route.ts) — All UTM sources
POST /report/all-leads                  -> ReportController (report.route.ts) — All leads report
POST /report/download-refund            -> ReportController (report.route.ts) — Download refund Excel
POST /report/landing-partner-leads      -> ReportController (report.route.ts) — Landing partner leads
POST /report/collection-emi             -> ReportController (report.route.ts) — Collection EMI report
POST /report/settlement                 -> ReportController (report.route.ts) — Settlement report
POST /report/collection-mode            -> ReportController (report.route.ts) — Collection mode report
POST /report/disbursal-summary          -> ReportController (report.route.ts) — Disbursal summary report
POST /report/event-funnel               -> EventFunnelController (report.route.ts) — Event funnel
```

### User Management
```
GET  /user/list                          -> UserController (user.route.ts) — Management user list
POST /user/add                           -> UserController (user.route.ts) — Add user
POST /user/edit/:userID                  -> UserController (user.route.ts) — Edit user
GET  /user/download-list                 -> UserController (user.route.ts) — Download user list Excel
GET  /user/report-access/:userID         -> UserController (user.route.ts) — Get report access
POST /user/report-access/update          -> UserController (user.route.ts) — Update report access
GET  /user/login-logs                    -> UserController (user.route.ts) — Login logs
GET  /user/whitelist-ips                 -> UserController (user.route.ts) — Whitelist IPs
POST /user/whitelist-ip/add              -> UserController (user.route.ts) — Add whitelist IP
DELETE /user/whitelist-ip/:id            -> UserController (user.route.ts) — Delete whitelist IP
GET  /user/roles                         -> UserController (user.route.ts) — Get roles list
GET  /user/role/:roleId                  -> UserController (user.route.ts) — Get role details
POST /user/role/add                      -> UserController (user.route.ts) — Add role
POST /user/role/edit/:roleId             -> UserController (user.route.ts) — Edit role
GET  /user/permissions                   -> UserController (user.route.ts) — Get permissions list
GET  /user/permission/:permissionId      -> UserController (user.route.ts) — Get permission details
POST /user/permission/add                -> UserController (user.route.ts) — Add permission
POST /user/permission/edit/:permissionId -> UserController (user.route.ts) — Edit permission
GET  /user/role-permissions/:roleId      -> UserController (user.route.ts) — Get role permissions
POST /user/role-permissions/update/:roleId -> UserController (user.route.ts) — Update bulk role permissions
GET  /user/dashboard                     -> UserController (user.route.ts) — Dashboard stats
GET  /user/permissions-list              -> UserController (user.route.ts) — All permissions list
GET  /user/permissions-types             -> UserController (user.route.ts) — Permission types
GET  /user/:userID                       -> UserController (user.route.ts) — Get user by ID
```

### Blacklist
```
POST /blacklist/blacklist-list           -> BLACKLISTController (blacklist.route.ts) — Blacklisted customer list
```

### Document
```
POST /document/finbox-doc-list           -> DocumentController (document.route.ts) — Finbox doc list
POST /document/pdf-url                   -> DocumentController (document.route.ts) — PDF URL by ID
POST /document/name-dob-match            -> DocumentController (document.route.ts) — Name/DOB match
POST /document/link-aadhar-pan-reverify  -> DocumentController (document.route.ts) — Link Aadhaar-PAN reverify
POST /document/finbox-check-fraud        -> DocumentController (document.route.ts) — Finbox fraud check
```

### Logs
```
POST /logs/update-sms-logs               -> LogsController (logs.routes.ts) — Update SMS logs
POST /logs/api-logs                      -> LogsController (logs.routes.ts) — Get API logs
POST /logs/logs-view                     -> LogsController (logs.routes.ts) — Logs view
POST /logs/migrate                       -> LogsController (logs.routes.ts) — Migrate leads API logs
```

### History
```
POST /history/loan-history               -> HistoryController (history.route.ts) — Loan history
POST /history/lead-history               -> HistoryController (history.route.ts) — Lead history
POST /history/address-history            -> HistoryController (history.route.ts) — Address history
POST /history/add-address                -> HistoryController (history.route.ts) — Add address
POST /history/employment-history         -> HistoryController (history.route.ts) — Employment history
POST /history/salary-history             -> HistoryController (history.route.ts) — Salary history
POST /history/location-history           -> HistoryController (history.route.ts) — Location history
POST /history/account-aggregator         -> HistoryController (history.route.ts) — Account aggregator history
POST /history/email-history              -> HistoryController (history.route.ts) — Email history
```

### SOA
```
POST /soa/generate-pdf                   -> SoaController (soa.route.ts) — Generate SOA PDF
POST /soa/section-data                   -> SoaController (soa.route.ts) — Sanction data
```

### Refund
```
POST /refund/razorpay-refund             -> RefundController (refund.route.ts) — Razorpay refund
POST /refund/bulk-refund                 -> RefundController (refund.route.ts) — Bulk refund
POST /refund/upload-bulk-refund          -> RefundController (refund.route.ts) — Upload bulk refund file
POST /refund/user-refund-report          -> RefundController (refund.route.ts) — User refund report
POST /refund/download-refund-report      -> RefundController (refund.route.ts) — Download refund report Excel
POST /refund/refund-files                -> RefundController (refund.route.ts) — Get refund files
POST /refund/get-updated-refund-file     -> RefundController (refund.route.ts) — Get updated refund file
POST /refund/get-refund-file-url         -> RefundController (refund.route.ts) — Get refund file URL
POST /refund/refund-dashboard-summary    -> RefundController (refund.route.ts) — Refund dashboard summary
```

### Quick Report
```
POST /quick-report/menu                  -> QuickReportController (quickReport.route.ts) — Menu
POST /quick-report/reports               -> QuickReportController (quickReport.route.ts) — Get reports
POST /quick-report/download              -> QuickReportController (quickReport.route.ts) — Download report
```

### Projection
```
POST /projection/upload                  -> ProjectionController (projection.route.ts) — Upload projection file
POST /projection/report                  -> ProjectionController (projection.route.ts) — Projection report
POST /projection/failed-file             -> ProjectionController (projection.route.ts) — Failed file
POST /projection/call-monitoring         -> ProjectionController (projection.route.ts) — Call monitoring data
POST /projection/call-description        -> ProjectionController (projection.route.ts) — Call description data
GET  /projection/failed-details          -> ProjectionController (projection.route.ts) — Failed projection details
```

### Common
```
POST /common/experian-user-details       -> CommonController (common.route.ts) — Experian user details
POST /common/experian-crm-details        -> CommonController (common.route.ts) — Experian CRM details
POST /common/experian-bureau-details     -> CommonController (common.route.ts) — Experian bureau details
POST /common/stepper                     -> CommonController (common.route.ts) — Stepper update
POST /common/data-update                 -> CommonController (common.route.ts) — Data update
GET  /common/lead-statuses               -> CommonController (common.route.ts) — Get lead statuses
```

### Filter
```
POST /filter/filter                      -> FilterController (filter.route.ts) — Get filters by page
```

### App Function
```
POST /app-function/holiday-list          -> AppFunctionController (appFunction.route.ts) — Holiday list
POST /app-function/add-holiday           -> AppFunctionController (appFunction.route.ts) — Add holiday
POST /app-function/delete-holiday        -> AppFunctionController (appFunction.route.ts) — Delete holiday
POST /app-function/disb-status           -> AppFunctionController (appFunction.route.ts) — Get disbursal status
POST /app-function/update-disb-status    -> AppFunctionController (appFunction.route.ts) — Update disbursal status
POST /app-function/gateway-type          -> AppFunctionController (appFunction.route.ts) — Get gateway type
POST /app-function/update-gateway-type   -> AppFunctionController (appFunction.route.ts) — Update repayment gateway type
```

### Bulk Upload Collection
```
POST /bulk-upload/upload                 -> bulkUploadCollection (bulkUploadCollection.route.ts) — Upload collection CSV
POST /bulk-upload/history-log            -> bulkUploadCollection (bulkUploadCollection.route.ts) — History log with pagination
POST /bulk-upload/download-excel         -> bulkUploadCollection (bulkUploadCollection.route.ts) — Download group-wise Excel
```

### DSA
```
GET  /dsa/list                           -> DsaController (dsa.route.ts) — List DSA
POST /dsa/create                         -> DsaController (dsa.route.ts) — Create DSA
POST /dsa/update                         -> DsaController (dsa.route.ts) — Update DSA
POST /dsa/delete                         -> DsaController (dsa.route.ts) — Delete DSA
POST /dsa/upload-emis                    -> DsaController (dsa.route.ts) — Upload DSA EMI file
POST /dsa/mis-report                     -> DsaController (dsa.route.ts) — MIS report
POST /dsa/download-mis-report            -> DsaController (dsa.route.ts) — Download MIS report
POST /dsa/credit-links                   -> DsaController (dsa.route.ts) — Credit links
```

### Waiver
```
POST /waiver/create                      -> WaiverController (waiver.route.ts) — Create waiver
POST /waiver/action                      -> WaiverController (waiver.route.ts) — Waiver action
POST /waiver/bulk-action                 -> WaiverController (waiver.route.ts) — Bulk waiver action
POST /waiver/list                        -> WaiverController (waiver.route.ts) — Waiver list
POST /waiver/cancel/:collectionID        -> WaiverController (waiver.route.ts) — Cancel waive-off
POST /waiver/manager                     -> WaiverController (waiver.route.ts) — Waiver manager
```

### Contact Us
```
POST /contact-us/data                    -> ContactUsController (contactUs.route.ts) — Contact us data
POST /contact-us/excel                   -> ContactUsController (contactUs.route.ts) — Contact us Excel
```

### Deep Link
```
GET  /deeplink/:referrer                 -> DeepLinkController (deeplink.route.ts) — Deep link redirect
```

### Report Summary
```
GET  /report-summary                     -> ReportController (reportSummary.route.ts) — Report summary
```

### Lentra Report
```
POST /lentra-report/failed-loans         -> LentraReportController (lentraReport.route.ts) — Failed loan report
POST /lentra-report/export-failed-loans  -> LentraReportController (lentraReport.route.ts) — Export failed loans
```

### Customer Data Update
```
POST /customer-data-update/update        -> CustomerDataUpdateController (customerDataUpdate.routes.ts) — Update customer data with history
```

### Index
```
GET  /                                   -> IndexController (index.route.ts) — Health check / root
```

---

## DATA_MODELS

### MySQL (Knex-based models)

`IAddress (src/database/mysql/address.ts)` — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy

`IApproval (src/database/mysql/approval.ts)` — fields: approvalID, customerID, leadID, loanType, productType, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, plateFormFee, convinineceFee, creditRiskAnalisys, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, activeLoans, activePL, activeHL, activeCC, activePaydayLoan, outstandingAmount, monthlyObligation, status, formNo, employed, remark, loanRequirePurpose, creditedBy, rejectionReason, documentr, redFlag, createdDate, sanctionalloUID, customerApproval, employmentType, m1-m3, m_avg, p1-p3, m1_date-m3_date, disbursalRemark

`ILead (src/database/mysql/leads.ts)` — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, commingLeadsDate, ip, callAssign, creditAssign, createdDate, alloUID, sanctionalloUID, sanctionAppID, entity_id, field_officer_id, em_id, step, kfs, bureauVersion, bankingSurrogateVersion, MLresponse, MLfeatures, MLamount, MLsalary, mlDateTime, productID, ipc, hold_date, hold_time, iu_date, lenderID, kfs_ip

`ICustomer (src/database/mysql/customer.ts)` — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, dob_digit_match_btn_click, sim_available, emandate_required, email_verification_status, email_delivery_status, email_last_validation, step, ckyc_status

`ILoan (src/database/mysql/loan.ts)` — fields: loanID, leadID, lenderID, loanNo, customerID, approvalID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, accountNo, accountType, bankIfsc, bank, bankBranch, chequeDetails, pdDate, pdDoneBy, repayDate, deduction, remarks, status, rejReason, companyAccountNo, ip, disbursedBy, createdDate, allocate_date, allocated_by, is_manual, manual_date, utr, payout_status, cooling_period_flag, cooling_period_date

`ICredit (src/database/mysql/credit.ts)` — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, actualTenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, paneltyEmis, status, principal, amountToBeRepayed, firstDueDate, brokenPeriodIntrest, gst, created_at, disbursalDate

`IEmi (src/database/mysql/emi.ts)` — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paneltyID, paymentID, status, amountRemains, createdAt, updatedAt, amountRemainsInterest, amountRemainsPenalty, amountRemainsBrokenPeriodIntrest, brokenPeriodIntrest, accessAmount, color, bgcolor, paymentReceived, is_deleted, waive_off_amount

`ICollection (src/database/mysql/collection.ts)` — fields: collectionID, customerID, leadID, loanNo, collectedAmount, penaltyAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, createdDate, collectionStatus, collectionStatusby, approvedDate, orderID, excess_amount, discount_waiver, discount_waiver_amount, refund_utr_no, opening_balance, closing_balance, total_interest, principal_amount, penality_charge, collected_interest, collected_principal, collected_penality, updated_date, collectedDateIST, refundType, refundRemarks, approvedBy, amount, mode, remarks

`ICustomerAccount (src/database/mysql/customerAccount.ts)` — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, createdDate, bank_holder_name, is_credit, isAadharVerified

`IDocument (src/database/mysql/document.ts)` — fields: documentID, customerID, leadID, documentType, documentFile, password, status, verifiedBy, verifiedDate, uploadBy, uploadedDate, type, upload_platform, iu_date

`IDocumentFinbox (src/database/mysql/documentFinbox.ts)` — fields: documentID, customerID, leadID, entityID, type, statement_id, documentType, documentFile, verifiedBy, status, verifiedDate, uid, aa_check, iu_date

`IEmployer (src/database/mysql/employer.ts)` — fields: employerID, customerID, leadID, employerName, empEmail, empDob, empSalary, empDesignation, empWorkIndustry, employment, totalExperience, currentCompany, address, city, state, pincode, status, verifiedBy, createdDate, office_email_id, office_email_otp, is_verified_email

`IReferenceModel (src/database/mysql/reference.ts)` — fields: referenceID, customerID, relation, name, address, city, state, pincode, contactNo, createdBy, createdDate, name_contact, reference_verify, is_verified, recording, upload_platform

`IPennyDropModel (src/database/mysql/pennyDrop.ts)` — fields: id, customerID, p_id, leadID, name, ifsc, bank_name, account_number, account_status, registered_name, credated_date, logs, penny_status, uid, penny_drop_name_match, penny_type

`IRazorpayMandate (src/database/mysql/razorpay_mandate.ts)` — fields: id, customerID, accountNo, accountType, bank, ifsc, leadID, inv_id, entity, receipt, invoice_number, customer_id, cust_name, cust_email, cust_contact, order_id, status, sms_status, email_status, short_url, type, credated_date, uid, devices, etype, token_id, emMaxamount, res_response, need_another_mandate, name_missmatch_reject, payment_id

`IRazorpayEMOrder (src/interfaces/razorpay_emOrder.ts)` — fields: id, emID, customerID, leadID, orderID, entity, amount, amount_paid, amount_due, currency, receipt, remarks, status, notes_key_1, razorpay_payment_id, razorpay_order_id, razorpay_signature, tokenID, uid, createdDate

`IRazorpayPayoutDisbursedAmount (src/database/mysql/razorpay_payout_disbured_amount.ts)` — fields: disID, disbDate, id, entity, fund_account_id, amount, currency, notes_key_1, notes_key_2, fees, tax, status, utr, mode, purpose, reference_id, narration, batch_id, description, source, reason, merchant_id, status_details_id, customerID, leadID, creadatedDate, failure_reason, uid, reamrk, api_log, bank_changed, is_checked

`IRazorpaySubscription (src/database/mysql/razorpay_subscription.ts)` — fields: id, customerID, startAt, endAt, status, cancelled_date, productID, razorpay_response, razorpay_subscription_id, createdAt, updatedAt

`ILentraCustomerMapping (src/database/mysql/lentra_customer_mapping.ts)` — fields: id, customerID, leadID, lms_id, los_id, loan_no, entity_id, bank_details_id, created_at, updated_at, isNachNeeded, nachMandateId, nachStatus, stpStatus, mandateCanceled, workflow_id, reference_id, stp_retries, nach_retries, nach_cancel_retries

`IUser (src/database/mysql/users.ts)` — fields: userID, name, email, mobile, did_no, branch, userName, password, role, status, createdBy, createdDate, accessPer, utype, firebase_token, device_token, lip, convoque_login_id, convoque_exten, whatsapp_email, lead_status, otp, password_updated_at, mac_address, random_id, mac_otp, utmSource, sessionID, iu_date

`IRole (src/database/mysql/roles.ts)` — fields: role_id, role_name, role_display_name, status, created_at, created_by, updated_at, updated_by

`IPermission (src/database/mysql/permissions.ts)` — fields: permission_id, permission_name, permission_display_name, permission_type, status, created_by, created_at, updated_at, updated_by

`IRolePermissionLinks (src/interfaces/role_permission_links.interface.ts)` — fields: id, role_id, permission_id, status, created_at, created_by, updated_at, updated_by, iu_date

`ICustomerDnd (src/database/mysql/customerDnd.ts)` — fields: id, name, customerID, mobile, reason, start_date, expiry_date, created_at, updated_at, pancard, updated_by, is_deleted, removed_by, updatedName, removedName

`IDsa (src/database/mysql/dsa.ts)` — fields: id, dsa_name, min_age, max_age, employment, min_salary, min_income_se, geography, credit_score, min_loan_amount, max_loan_amount, tenure_min_months, tenure_max_months, pf_starting, interest_starting, is_deleted, created_at, updated_at

`ISourcePartner (src/database/mysql/source_partners.ts)` — fields: id, image, name, link, status, created_at, updated_at

`IRepayDateHolidayModel (src/database/mysql/repayDateHoliday.ts)` — fields: id, repaydate

`IRepaymentGatewayTypeModel (src/database/mysql/repayment_gateway_type.ts)` — fields: id, gateway_type, hard_status, created_at, updated_at

`IAutoDisbStatus (src/database/mysql/auto_disb_status.ts)` — fields: id, auto_disb_status

`ILoginLogs (src/database/mysql/loginLogs.ts)` — fields: id, userID, name, email, ip, loginStart, loginEnd, iu_date

`IReportLog (src/database/mysql/reportLog.model.ts)` — fields: id, user_id, user_name, report_name, requested_url, requested_params, ip_address, created_at, updated_at

`IBankUpdateCheckModel (src/database/mysql/bank_update_check.ts)` — fields: id, customerID, leadID, data

`IDisbursalJobsModel (src/database/mysql/disbursal_jobs.ts)` — fields: id, customerID, leadID, loanID, loanNo, accountNo, ifsc, actualDisbAmount, custName, custMobile, custEmail, companyAcc, userID, createdDate, currentStatus, jobStatus, apiStatus

`IMobileToken (src/database/mysql/mobileToken.ts)` — fields: id, customerID, mobile, appID, credatedDate, imei, access_token, last_login, android_id, firebase_token, jwt_access_token

`ICustomerHistory (src/interfaces/customerHistory.interface.ts)` — fields: id, customerID, changedBy, changeType, tableName, fieldName, oldValue, newValue, changeReason, ipAddress, userAgent, createdAt

`IWhitelistIP (src/database/mysql/user_ip_details.ts)` — fields: id, ip, status, added_by

`IMobileDecryptionLog (src/database/mysql/mobile_decryption_log.ts)` — fields: id, user_id, decrypted_mobile, created_at, updated_at

`ICollectionFollowUp (src/database/mysql/collectionFollowUp.ts)` — fields: reviewID, customerID, leadID, loanNo, followType, StatusType, statusTypeDate, remark, createdBy, createdDate, followup_type, reason, iu_date

`INoLoanFollowUpLogs (src/database/mysql/no_loan_follow_up_logs.ts)` — fields: id, lead_id, customer_id, follow_up_by, follow_type, status_type, remark, created_at, updated_at, iu_date

`IKalyeraLog (src/database/mysql/kaleyraLogs.ts)` — fields: (MySQL table-mapped; see also Mongo model)

`ICallHistoryLog (src/database/mysql/callhistorylogs.ts)` — fields: callHistoryID, customerID, leadID, callType, status, appAmount, noteli, remark, callbackTime, calledBy, createdDate

`IOnlinePayment (src/database/mysql/onlinepayment.ts)` — fields: pID, name, email, phone, service, typeProduct, toValue, message, razorpayOrderId, razorpayPaymentId, paymentStatus, makerstamp, updatestamp, status, approved_id, paymentType, method, leadID, device

`ITransection (src/database/mysql/transections.ts)` — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, deleted, gateway, createdAt, updatedAt, createdBy, updatedBy, amount, collectionID, emiID, transactionDate, remarks, payment_transaction_status, waiver, discount_type

`IUserMetadata (src/database/mysql/user_metadata.ts)` — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image, created_at, updated_at

`IReportAccess (src/interfaces/reports.interface.ts)` — fields: id, name, procedure, input, created_at, updated_at, delete, date

`IVirtualAccount (src/database/mysql/virtualAccount.ts)` — fields: accID, customerID, leadID, accounID, name, customer_id, recid, entity, ifsc, bankName, recName, account_number, credatedDate, uid, iu_date

`IWhatsappMessageIds (src/database/mysql/whatsapp_message_ids.ts)` — fields: id, wc_id, template_name, leadID, lead_status, send_from, user_id, created_at, updated_at, iu_date

`ICreditReport (src/database/mysql/credit_report.ts)` — fields: id, cr_provider, bucket_id, customerID, stage_one_id, stage_two_id, errors, status, score, response_time, initiated_by, action_type, cb_mark, created_by, log_id, created_at, updated_at, updated_by, unique_cust_id

`ICreditScoreUserJourney (src/database/mysql/credit_socore_user_journey.ts)` — fields: id, step, attempt, customerID

`ISubscriptionPayment (src/database/mysql/subscription_payments.ts)` — fields: id, customerID, subscriptionId, orderId, paymentId, amount, gst, totalAmount, status, response, createdAt, updatedAt

`ISubscriptionRefund (src/database/mysql/subscription_refund.ts)` — fields: id, pg_refund_id, amount, payment_id, status, subscriptionId, customerID, createdAt, updatedAt

`IStepTrackerModel (src/database/mysql/step_tracker.ts)` — fields: id, step_id, is_completed, created_at, updated_at, is_skippable, customer_id, lead_id

`IStepControlModel (src/database/mysql/step-control.ts)` — fields: id, product_id, provider_id, instrument_id, step_name, step_display_name, pre_step_name, pre_step_display_name, post_step_name, post_step_display_name, step_order, next_route, is_active, created_at, created_by, updated_by, updated_at, current_route, prev_route, dashboard_message1-4, should_recheck

`IEMITransaction (src/database/mysql/emiTransactions.ts)` — fields: transaction_id, order_id, emi_id, interest, principal, penalty, dpd_amount, transaction_date, lead_id, emi_status

`IMailTemplate (src/database/mysql/mail_template.ts)` — fields: id, name, subject, message

`INotification (src/database/mysql/notification.ts)` — fields: notificationID, customerID, leadID, notification, type, subject, createdDate, mtype, uid

`IPaymentMode (src/database/mysql/paymentMode.ts)` — fields: id, mode, status, id_date

`IPaymentModeForBanks (src/database/mysql/payment_mode_for_banks.ts)` — fields: id, bank_name, payment_mode, created_by, created_date, updated_by, updated_date, status, id_date

`IRefundReasons (src/database/mysql/refundReasons.ts)` — fields: reasonID, reason, isActive

`IBankIfscModel (src/database/mysql/bankIfsc.ts)` — fields: id, BANK, IFSC, BRANCH, CENTRE, DISTRICT, STATE, ADDRESS, CONTACT, IMPS, RTGS, CITY, ISO3166, NEFT, MICR, UPI, SWIFT, is_active

`ICallDisposition (src/database/mysql/call_disposition.ts)` — fields: id, call_date, call_time, loan_no, agent_name, campaign, disposition, sub_disposition, callback_time, next_action_datetime, ptp_amount, remarks, lot_name, branch_name, customer_name, customer_email, customer_mobile, loan_amount, due_date_repay_amount, repay_amount, disbursed_date, repay_date, remaining_collection, total_collection, loan_tenure, roi, address, call_landing_time, call_duration, disposition_duration, end_call_time, hangup_by

`IWhatsappDisposition (src/database/mysql/whatsapp_disposition.ts)` — fields: id, phone_number, country_code, customer_name, failed, failure_reason, sent_timestamp, delivered_timestamp, read_timestamp, replied_timestamp, campaign_owner_email, loan_no

`ICustomerAppLocation (src/database/mysql/customerAppLocation.ts)` — fields: id, mobile, customerID, residenceAddress, state, city, pincode, created_at

`ICustomerSalary (src/database/mysql/customerSalary.ts)` — fields: id, customerID, salary_date, particulars, amount, createdBy, created_at

`IFinboxClientUrl (src/database/mysql/finboxClientUrl.ts)` — fields: id, leadID, customerID, url, uid, credated_date

`IEmandateNotRequiredLogsModel (src/database/mysql/emandate_not_required_logs.ts)` — fields: id, customerID, nr_startBy, nr_startDate, nr_endBy, nr_endDate, last_emandate_paid

`IAutoDisbStatusLog (src/database/mysql/auto_disb_status_log.ts)` — fields: changed_status, changed_by

`IAutoDisbursalLogsModel (src/database/mysql/auto_disbursal_logs.ts)` — fields: id, customerID, leadID, api_request, api_response, userID, any_error, status, createdDate

`IRazorPayMandateStatusModel (src/database/mysql/razorpay_mandate_status.ts)` — fields: id, emId, leadID, customer_id, inv_id, emstatus, credated_date, tokenID, accountNo, accountType, bank, ifsc

`IRazorPayPayoutAccountsModel (src/database/mysql/razorpay_payout_accounts.ts)` — fields: payaccID, customerID, leadID, acc_id, entity, contact_id, account_type, ifsc, bank_name, name, account_number, active, batch_id, createdDate, uid

`IRazorPayPayoutContactsModel (src/database/mysql/razorpay_payout_contact.ts)` — fields: payoutID, customerID, leadID, cont_id, cont_entity, cont_name, cont_contact, cont_email, cont_type, cont_reference_id, cont_batch_id, cont_active, cont_notes_key_1, cont_notes_key_2, createdDate, uid, iu_date

`IUserLoginAttempt (src/database/mysql/user_login_attempt.ts)` — fields: userID, login_attempt, otp_attempt, last_attempt

`IUserSummary (src/database/mysql/user_summary.ts)` — fields: id, api_type, customerID, provider_id, json_value, Status, created_at, created_by, updatedAt

`ICustomerBlackListModel (src/database/mysql/blackListCustomer.ts)` — fields: id, customerid, leadid, email, mobile, date, uid, lead_status, message, iu_date

`IBlacklistCustomerPancard (src/database/mysql/blacklistCustomerPancard.ts)` — fields: id, pancard, status, addBy, addDate, removeBy, removeDate, createdDate, reason

`IApiReqResLog (src/database/mysql/api_req_res_log.ts)` — fields: id, customerID, mobile, api_request, api_response, created_at, status, message, api_name

`ILeadsApiLog (src/database/mysql/lead_api_log.ts)` — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo, code, state, entity_id, sync_id, sync_result, sync_data, amount

`IRazorpayLog (src/database/mysql/razorpay_logs.ts)` — fields: id, customerID, leadID, req_url, api_request, api_response, type, created_at

`ISendInblueLog (src/database/mysql/send_inblue_log.ts)` — fields: id, customer_id, iu_date, api_response, type, updated_at, created_at

`IChatLog (src/database/mysql/chat_logs.ts)` — fields: id, leadID, agent_id, customer_reply, customer_number, message, messgae_json, status, created_at, api_request, api_response, message_id, msg_seen, document_type, cron_msg_send, iu_date

`IDialerLog (src/database/mysql/dialer_log.ts)` — fields: id, lead_id, mobile_no, user_id, api_type, api_trace_id, api_message, api_status, api_response, created_at, src, customer_no, call_start_time, call_end_time, agent_ring_time, agent_talk_time, call_status, hangup_cause, hangup_text, unique_id, callback_created_at, iu_date

`IWhatsappLog (src/database/mysql/whatsapp_log.ts)` — fields: id, customer_id, id_date, response, type, updated_at, created_at

`IAppInstallationsLog (src/database/mysql/app_installation_log.ts)` — fields: apps, created_at, customerID, id, iu_date, updated_at

`IAppVideoModel (src/database/mysql/appVideo.ts)` — fields: vid, customerID, leadID, vSize, viFile, vUrl, credated_date, upload_platform, rejected_status

`ICity (src/database/mysql/cities.ts)` — fields: cityID, stateID, cityName, status, createdDate

`IState (src/database/mysql/states.ts)` — fields: stateID, stateName, status, createdDate, code, cibil_state_code

`IProduct (src/database/mysql/product.ts)` — fields: productID, name, logo, discription, type, step, status, leadID, customerID

`IOtherCharges (src/database/mysql/other_charges.ts)` — fields: id, emiID, creditID, amount, customerID, transectionID, discription, status, leadID, loanID

`IOnlinePaymentLog (src/database/mysql/onlinepaymentlog.ts)` — fields: id, pID, razorpayOrderId, razorpayPaymentId, paymentStatus, createdDate

`IEMITransaction (src/database/mysql/emiTransactions.ts)` — fields: transaction_id, order_id, emi_id, interest, principal, penalty, dpd_amount, transaction_date, lead_id, emi_status

`IFinboxNameMismatchModel (src/interfaces/finboxNameMismatch.interface.ts)` — fields: id, customerID, leadID, accountNo, firstName, secondName, percentageMatch, status, action_by, createdDate, id_date

`ILentraMaintainanceModel (src/interfaces/lentra.interface.ts)` — fields: id, downtime_start, downtime_end, reason, is_active, created_at, updated_at

### Prisma / MySQL (schema.prisma)

`User (src/database/prisma/schema.prisma)` — fields: id (Int, PK), email (String, unique), password (String)

### MongoDB (Mongoose)

`CustomerAssetData (src/database/mongo/model/CustomerAssetData.ts)` — fields: userId (Number), leadId (Number), shakey (String), customerAsset (Any) — relationships: none

`EmiAutoPaymentCronLog (src/database/mongo/model/EmiAutoPaymentCronLog.ts)` — fields: emiIDs (Number[]), individualRecord ([{emiID, razorpay_mendate_id, status, errorMessage, step}]), createdAt, updatedAt — relationships: none

`KaleyraLogs (src/database/mongo/model/KaleyraLogs.ts)` — fields: mobile (String), req_url (String), api_request (Any), api_response (Any), curl_error (String), type (String), created_at (Date) — relationships: none

`RazorpayRefundLogs (src/database/mongo/model/RazorpayRefundLogs.ts)` — fields: leadID, customerID, loanNo, refund_id, payment_id, order_id, refund_amount, excess_amount, status, refund_mode, reason, product_id, fileName, folderName, utr, created_at, processed_at, uid, name, mobile, email, pancard — relationships: none

`RazorpayWebhookLogs (src/database/mongo/model/RazorpayWeebhookLogs.ts)` — fields: id (ObjectId), subscriptionId (String), response (String), createdAt, updatedAt — relationships: none

`User (src/database/mongo/model/User.ts)` — fields: name (String), email (String, optional), password (String, optional) — relationships: none

`LentraLogs (src/models/lentraLogs.model.ts)` — fields: apiRequest (Object), apiResponse (Object), apiType (String), customerID (Number), leadID (Number), createdAt, updatedAt — relationships: none