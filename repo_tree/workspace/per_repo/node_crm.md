## ARCHITECTURE
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

## ROUTES
All routes are prefixed as registered in `src/routes/index.ts`. Exact prefixes are inferred from route files.

### Login (`/login` or similar)
`POST /login  →  LoginController.login  (src/routes/login.route.ts)  — Authenticate user`
`POST /verify-otp  →  LoginController.verifyOtp  (src/routes/login.route.ts)  — Verify login OTP`
`POST /forgot-password  →  LoginController.forgotPassword  (src/routes/login.route.ts)  — Request password reset`
`POST /update-password  →  LoginController.updatePassword  (src/routes/login.route.ts)  — Update user password`
`POST /validate-otp  →  LoginController.validateOtp  (src/routes/login.route.ts)  — Validate OTP with random_id`
`POST /login-with-mac  →  LoginController.loginWithMac  (src/routes/login.route.ts)  — MAC-address-based login`
`POST /assign-mac  →  LoginController.assignMacAddress  (src/routes/login.route.ts)  — Assign MAC address to user`
`POST /login-validation  →  LoginController.loginValidation  (src/routes/login.route.ts)  — Validate login code`

### Lead (`/lead` or similar)
`POST /lead/list  →  LEADController.unprocessedListv2  (src/routes/lead.route.ts)  — Paginated unprocessed lead list`
`POST /lead/credit-list  →  LEADController.creditList  (src/routes/lead.route.ts)  — Credit team lead list`
`POST /lead/sanction-list  →  LEADController.sanctionList  (src/routes/lead.route.ts)  — Sanction team lead list`
`POST /lead/again-no-loan  →  LEADController.againNoLoanList  (src/routes/lead.route.ts)  — Again-no-loan lead list`
`POST /lead/no-eligible  →  LEADController.noEligibleList  (src/routes/lead.route.ts)  — Not-eligible lead list`
`POST /lead/change-status  →  LEADController.changeLeadStatus  (src/routes/lead.route.ts)  — Update lead status`
`POST /lead/profile  →  LEADController.getProfileByLeadId  (src/routes/lead.route.ts)  — Get lead profile`
`POST /lead/loan-details  →  LEADController.getLoanDetails  (src/routes/lead.route.ts)  — Get lead loan details`
`POST /lead/add-collection  →  LEADController.addCollectionDetails  (src/routes/lead.route.ts)  — Add payday collection`
`POST /lead/add-emi-collection  →  LEADController.addEmiCollectionDetails  (src/routes/lead.route.ts)  — Add EMI collection`
`POST /lead/no-dues  →  LEADController.noDuesByLead  (src/routes/lead.route.ts)  — Generate no-dues PDF`
`POST /lead/soa  →  LEADController.generateSoaByLeadId  (src/routes/lead.route.ts)  — Generate SOA`
`POST /lead/download-collection-csv  →  LEADController.downloadCollectionCSV  (src/routes/lead.route.ts)  — Download CSV`
`POST /lead/excel-download  →  LEADController.excelDownload  (src/routes/lead.route.ts)  — Download lead Excel`
`POST /lead/check-penny-drop  →  LEADController.checkPennyDrop  (src/routes/lead.route.ts)  — Trigger penny drop`
`POST /lead/bank-update-check  →  LEADController.bankUpdateCheck  (src/routes/lead.route.ts)  — Bank update verification`
`POST /lead/bank-update  →  LEADController.bankUpdate  (src/routes/lead.route.ts)  — Update bank account`
`POST /lead/disbursal-update  →  LEADController.disbursalUpdate  (src/routes/lead.route.ts)  — Update disbursal`
`POST /lead/modify-loan  →  LEADController.modifyLoan  (src/routes/lead.route.ts)  — Modify payday loan`
`POST /lead/modify-emi-loan  →  LEADController.modifyEmiLoan  (src/routes/lead.route.ts)  — Modify EMI loan`
`POST /lead/auto-allocation  →  LEADController.autoallocation  (src/routes/lead.route.ts)  — Auto-allocate lead`
`POST /lead/allocate-to-me  →  LEADController.allocateToMe  (src/routes/lead.route.ts)  — Allocate lead to self`
`POST /lead/add-collection-followup  →  LEADController.addCollectionFollowup  (src/routes/lead.route.ts)  — Add follow-up`
`POST /lead/reference-details  →  LEADController.addReferenceDetails  (src/routes/lead.route.ts)  — Save references`
`POST /lead/blacklist-customer  →  LEADController.blacklistCustomerAdd  (src/routes/lead.route.ts)  — Blacklist customer`
`POST /lead/sync-whitelist  →  LEADController.syncWhitelistRamfin  (src/routes/lead.route.ts)  — Sync whitelist`
`POST /lead/generate-emandate  →  LEADController.generateEmandate  (src/routes/lead.route.ts)  — Generate e-mandate`
`POST /lead/charge-emandate  →  LEADController.chargeEmandate  (src/routes/lead.route.ts)  — Charge e-mandate`
`POST /lead/repayment-date  →  LEADController.updateRepaymentDate  (src/routes/lead.route.ts)  — Update repayment date`
`POST /lead/decrypt-mobile  →  LEADController.decryptMobile  (src/routes/lead.route.ts)  — Decrypt mobile number`
`GET /lead/trigger-loan-writeoff  →  LEADController.triggerLoanWriteOffByDate  (src/controllers/lead.controller.ts)  — Trigger write-off by date`

### CRM (`/crm`)
`PUT /crm/lead  →  CRMController.leadUpdate  (src/routes/crm.route.ts)  — Update lead record`
`POST /crm/emi-calculator  →  CRMController.emiCalculator  (src/routes/crm.route.ts)  — Calculate EMI`
`POST /crm/credit-details  →  CRMController.creditDetails  (src/routes/crm.route.ts)  — Save credit details`
`POST /crm/generate-emi  →  CRMController.generateEMI  (src/routes/crm.route.ts)  — Generate EMI schedule`
`POST /crm/update-payment  →  CRMController.updatePayment  (src/routes/crm.route.ts)  — Update payment via alt channel`
`POST /crm/apply-penalty  →  CRMController.applyPanelty  (src/routes/crm.route.ts)  — Apply penalty to EMI`
`GET /crm/emis  →  CRMController.getEmis  (src/routes/crm.route.ts)  — Get EMIs for customer`
`POST /crm/docs-requirements  →  CRMController.getDocsRequirements  (src/routes/crm.route.ts)  — Get doc requirements`
`POST /crm/emi-loan-details  →  CRMController.getEmiLoanDetails  (src/routes/crm.route.ts)  — Get EMI loan details`
`POST /crm/bulk-mandate-upload  →  CRMController.uploadBulkMandateFile  (src/routes/crm.route.ts)  — Upload bulk mandate file`
`GET /crm/bulk-mandate  →  CRMController.getBulkMandateData  (src/routes/crm.route.ts)  — List bulk mandate data`
`POST /crm/payday-to-emi  →  CRMController.paydayToEmiConversion  (src/routes/crm.route.ts)  — Convert payday to EMI`
`POST /crm/loan-agreement  →  CRMController.generateLoanAgreement  (src/routes/crm.route.ts)  — Generate loan agreement PDF`

### Collection (`/collection`)
`POST /collection/payday-pending  →  CollectionController.findPayDayPendingCollection  (src/routes/collection.route.ts)  — Payday pending collection list`
`GET /collection/payday-pending/excel  →  CollectionController.downloadPaydayPendingExcel  (src/routes/collection.route.ts)  — Download payday pending Excel`
`POST /collection/emi-pending  →  CollectionController.findEmiPendingCollection  (src/routes/collection.route.ts)  — EMI pending collection list`
`GET /collection/emi-pending/excel  →  CollectionController.downloadEmiPendingExcel  (src/routes/collection.route.ts)  — Download EMI pending Excel`
`POST /collection/allocate  →  CollectionController.addMultipleLeads  (src/routes/collection.route.ts)  — Allocate multiple leads`
`POST /collection/report  →  CollectionController.findCollectionReport  (src/routes/collection.route.ts)  — Collection report`
`GET /collection/report/excel  →  CollectionController.downloadCollectionReportExcel  (src/routes/collection.route.ts)  — Download collection report Excel`
`POST /collection/waive-off  →  CollectionController.addWaiveOff  (src/routes/collection.route.ts)  — Add waive-off request`
`GET /collection/waive-off/details  →  CollectionController.findWaiveOffLoanDetail  (src/routes/collection.route.ts)  — Waive-off loan details`
`POST /collection/dnd/list  →  CustomerController.getDND  (src/routes/collection.route.ts)  — DND customer list`
`DELETE /collection/dnd  →  CustomerController.deleteDND  (src/routes/collection.route.ts)  — Remove DND entry`
`POST /collection/dnd  →  CustomerController.createDND  (src/routes/collection.route.ts)  — Add DND entry`
`PUT /collection/dnd  →  CustomerController.editDND  (src/routes/collection.route.ts)  — Edit DND entry`

### Customer (`/customer`)
`POST /customer/search  →  CustomerController.search  (src/routes/customer.routes.ts)  — Global customer search`
`POST /customer/list  →  CustomerController.getCustomerList  (src/routes/customer.routes.ts)  — Customer list`
`PUT /customer  →  CustomerController.updateCustomerDetails  (src/routes/customer.routes.ts)  — Update customer details`
`POST /customer/pan-verify  →  CustomerController.panVerification  (src/routes/customer.routes.ts)  — Verify PAN`
`POST /customer/aadhar-otp  →  CustomerController.aadharVerificationGenerateOtp  (src/routes/customer.routes.ts)  — Aadhar OTP`
`POST /customer/aadhar-verify  →  CustomerController.aadharVerificationVerifyOtp  (src/routes/customer.routes.ts)  — Verify Aadhar OTP`
`POST /customer/ckyc  →  CustomerController.ckycFetch  (src/routes/customer.routes.ts)  — CKYC fetch`
`POST /customer/feedback  →  CustomerController.feedbackList  (src/routes/customer.routes.ts)  — Customer feedback list`
`POST /customer/source-partner  →  CustomerController.setSourcePartner  (src/routes/customer.routes.ts)  — Add source partner`
`PUT /customer/source-partner  →  CustomerController.editSourcePartner  (src/routes/customer.routes.ts)  — Edit source partner`
`GET /customer/source-partner  →  CustomerController.getSourcePartner  (src/routes/customer.routes.ts)  — List source partners`
`POST /customer/blacklist-pan  →  CustomerController.blacklistPanScript  (src/routes/customer.routes.ts)  — Bulk blacklist PANs (CSV)`

### Customer Data Update (`/customer-data-update`)
`POST /customer-data-update  →  CustomerDataUpdateController.updateCustomerData  (src/routes/customerDataUpdate.routes.ts)  — Update customer data with history`

### Disbursal (`/disbursal`)
`POST /disbursal/bank-update  →  DisbursalController.bank_update  (src/routes/disbursal.route.ts)  — Bank update queue list`
`GET /disbursal/export-manual  →  DisbursalController.export_manual_disbursal  (src/routes/disbursal.route.ts)  — Export manual disbursal Excel`
`POST /disbursal/import-manual  →  DisbursalController.import_manual_disbursal  (src/routes/disbursal.route.ts)  — Import manual disbursal`
`POST /disbursal/allocate  →  DisbursalController.disbursal_allocate  (src/routes/disbursal.route.ts)  — Allocate disbursals`
`POST /disbursal/initiate  →  DisbursalController.disbursal_initiate_service  (src/routes/disbursal.route.ts)  — Initiate auto disbursal`
`POST /disbursal/bank-update-failed  →  DisbursalController.bankUpdateRejectFailed  (src/routes/disbursal.route.ts)  — Mark bank update failed`

### Document (`/document`)
`POST /document/finbox-list  →  DocumentController.getFinboxDocList  (src/routes/document.route.ts)  — List Finbox documents`
`POST /document/pdf-url  →  DocumentController.pdfUrlById  (src/routes/document.route.ts)  — Get document PDF URL`
`POST /document/name-match  →  DocumentController.nameDobMatch  (src/routes/document.route.ts)  — Name/DOB match check`
`POST /document/pan-aadhar-reverify  →  DocumentController.linkAadharPanReverify  (src/routes/document.route.ts)  — Re-verify PAN/Aadhar link`
`POST /document/finbox-fraud  →  DocumentController.leadFinboxCheckFraud  (src/routes/document.route.ts)  — Check Finbox fraud`

### Report (`/report`)
`POST /report/customer-feedback  →  ReportController.findCustomerFeedbackReport  (src/routes/report.route.ts)  — Customer feedback report`
`POST /report/disbursal-data  →  ReportController.findDisbursalDataReport  (src/routes/report.route.ts)  — Disbursal data report`
`GET /report/disbursal-data/excel  →  ReportController.downloadDisbursalDataReportExcel  (src/routes/report.route.ts)  — Download disbursal Excel`
`POST /report/collection-data  →  ReportController.findCollectionDataReport  (src/routes/report.route.ts)  — Collection data report`
`GET /report/collection-data/excel  →  ReportController.downloadCollectionDataReportExcel  (src/routes/report.route.ts)  — Download collection Excel`
`POST /report/pending-payment  →  ReportController.findDateWisePendingPaymentReport  (src/routes/report.route.ts)  — Pending payment report`
`POST /report/date-wise-lead  →  ReportController.findDateWiseLeadReport  (src/routes/report.route.ts)  — Date-wise lead report`
`GET /report/date-wise-lead/excel  →  ReportController.downloadDateWiseLeadExcel  (src/routes/report.route.ts)  — Download lead Excel`
`POST /report/date-wise-collection  →  ReportController.findDateWiseCollectionReport  (src/routes/report.route.ts)  — Date-wise collection report`
`GET /report/date-wise-collection/excel  →  ReportController.downloadDateWiseCollectionExcel  (src/routes/report.route.ts)  — Download collection Excel`
`POST /report/app-issue  →  ReportController.findAppIssueReport  (src/routes/report.route.ts)  — App issue report`
`POST /report/refund  →  ReportController.findRefundReport  (src/routes/report.route.ts)  — Refund report`
`GET /report/refund/excel  →  ReportController.downloadRefundReportExcel  (src/routes/report.route.ts)  — Download refund Excel`
`GET /report/utm-sources  →  ReportController.findAllUtmSource  (src/routes/report.route.ts)  — All UTM sources`
`POST /report/all-leads  →  ReportController.findLeadsDetails  (src/routes/report.route.ts)  — All leads report`
`POST /report/event-funnel  →  EventFunnelController.getEventFunnel  (src/routes/report.route.ts)  — Event funnel report`
`POST /report/landing-partner  →  ReportController.findLandingPartnerLeadsReport  (src/routes/report.route.ts)  — Landing partner report`
`POST /report/collection-emi  →  ReportController.findCollectionEmiReport  (src/routes/report.route.ts)  — EMI collection report`
`POST /report/settlement  →  ReportController.findSettlementReport  (src/routes/report.route.ts)  — Settlement report`
`POST /report/collection-mode  →  ReportController.findCollectionModeReport  (src/routes/report.route.ts)  — Collection mode report`
`POST /report/disbursal  →  ReportController.findDisbursalReport  (src/routes/report.route.ts)  — Disbursal report`

### Report Summary
`POST /report-summary  →  reportSummary  (src/routes/reportSummary.route.ts)  — Report summary`

### Quick Report
`POST /quick-report  →  QuickReportController.getReports  (src/routes/quickReport.route.ts)  — Get stored procedure report`
`POST /quick-report/download  →  QuickReportController.download  (src/routes/quickReport.route.ts)  — Download quick report (xlsx/txt)`
`GET /quick-report/menu  →  QuickReportController.getMenu  (src/routes/quickReport.route.ts)  — Get report menu for user`

### Projection
`POST /projection/upload  →  ProjectionController.uploadProjectionFile  (src/routes/projection.route.ts)  — Upload projection file`
`POST /projection/call-monitoring  →  ProjectionController.callMonitoringData  (src/routes/projection.route.ts)  — Call monitoring data`
`POST /projection/call-description  →  ProjectionController.callDescriptionData  (src/routes/projection.route.ts)  — Call description data`
`POST /projection/report  →  ProjectionController.projectionReport  (src/routes/projection.route.ts)  — Projection report`
`GET /projection/failed-file  →  ProjectionController.projectionFailedFile  (src/routes/projection.route.ts)  — Get projection failed file`
`GET /projection/failed-details  →  ProjectionController.projectionFailedFileDetails  (src/routes/projection.route.ts)  — Failed file details`

### Refund
`POST /refund/razorpay  →  RefundController.razorpayRefund  (src/routes/refund.route.ts)  — Initiate Razorpay refund`
`POST /refund/razorpay-bulk  →  RefundController.razorpayBulkRefund  (src/routes/refund.route.ts)  — Bulk Razorpay refund`
`POST /refund/upload  →  RefundController.uploadBulkRefundFile  (src/routes/refund.route.ts)  — Upload bulk refund CSV`
`GET /refund/files  →  RefundController.refundFiles  (src/routes/refund.route.ts)  — List refund files`
`GET /refund/updated-file  →  RefundController.getUpdatedRefundFile  (src/routes/refund.route.ts)  — Get updated refund file`
`GET /refund/file-url  →  RefundController.getRefundFileUrl  (src/routes/refund.route.ts)  — Get presigned refund file URL`
`POST /refund/user-report  →  RefundController.userRefundReport  (src/routes/refund.route.ts)  — User refund report`
`GET /refund/user-report/excel  →  RefundController.downloadUserRefundReportExcel  (src/routes/refund.route.ts)  — Download user refund Excel`
`POST /refund/dashboard-summary  →  RefundController.dashboardSummary  (src/routes/refund.route.ts)  — Refund dashboard summary`

### Waiver
`POST /waiver  →  WaiverController.createWaiver  (src/routes/waiver.route.ts)  — Create waiver request`
`POST /waiver/action  →  WaiverController.waiverAction  (src/routes/waiver.route.ts)  — Approve/reject waiver`
`POST /waiver/bulk-action  →  WaiverController.bulkWaiverAction  (src/routes/waiver.route.ts)  — Bulk waiver action`
`POST /waiver/list  →  WaiverController.getWaiverList  (src/routes/waiver.route.ts)  — List waivers`
`DELETE /waiver/cancel  →  WaiverController.cancelWaiveOff  (src/routes/waiver.route.ts)  — Cancel waive-off`

### SOA
`POST /soa/generate  →  SoaController.generatePdf  (src/routes/soa.route.ts)  — Generate SOA PDF`
`POST /soa/section-data  →  SoaController.sectionData  (src/routes/soa.route.ts)  — Get sanction section data`

### History
`POST /history/loan  →  HistoryController.getLoanHistory  (src/routes/history.route.ts)  — Loan history`
`POST /history/lead  →  HistoryController.getLeadHistory  (src/routes/history.route.ts)  — Lead history`
`POST /history/address  →  HistoryController.getAddressHistory  (src/routes/history.route.ts)  — Address history`
`POST /history/add-address  →  HistoryController.addAddressHistory  (src/routes/history.route.ts)  — Add address`
`POST /history/employment  →  HistoryController.getEmploymentHistory  (src/routes/history.route.ts)  — Employment history`
`POST /history/salary  →  HistoryController.getSalaryHistory  (src/routes/history.route.ts)  — Salary history`
`POST /history/location  →  HistoryController.getLocationHistory  (src/routes/history.route.ts)  — Location history`
`POST /history/account-aggregator  →  HistoryController.getAccountAggregatorHistory  (src/routes/history.route.ts)  — AA history`
`POST /history/email  →  HistoryController.getEmailHistory  (src/routes/history.route.ts)  — Email history`

### Logs
`POST /logs/api  →  LogsController.getApiLogs  (src/routes/logs.routes.ts)  — Get API logs`
`POST /logs/sms-update  →  LogsController.updateSMSLogs  (src/routes/logs.routes.ts)  — Update SMS/Kaleyra logs`
`POST /logs/view  →  LogsController.getLogsView  (src/routes/logs.routes.ts)  — View log detail`
`POST /logs/migrate  →  LogsController.migrateLeadsApiLogs  (src/routes/logs.routes.ts)  — Migrate lead API logs`

### Blacklist
`POST /blacklist/list  →  BLACKLISTController.getBlacklist  (src/routes/blacklist.route.ts)  — Blacklisted customers list`

### Bulk Upload Collection
`POST /bulk-upload/upload  →  bulkUploadCollection.uploadCollectionBulkRecord  (src/routes/bulkUploadCollection.route.ts)  — Upload bulk collection CSV`
`POST /bulk-upload/history  →  bulkUploadCollection.findUploadCollectionHistoryLog  (src/routes/bulkUploadCollection.route.ts)  — Upload history log`
`POST /bulk-upload/download  →  bulkUploadCollection.downloadExcelGroupWiseData  (src/routes/bulkUploadCollection.route.ts)  — Download group Excel`

### DSA
`GET /dsa  →  DsaController.getAllDsa  (src/routes/dsa.route.ts)  — List all DSA`
`POST /dsa  →  DsaController.createDsa  (src/routes/dsa.route.ts)  — Create DSA`
`PUT /dsa  →  DsaController.updateDsa  (src/routes/dsa.route.ts)  — Update DSA`
`DELETE /dsa  →  DsaController.deleteDsa  (src/routes/dsa.route.ts)  — Delete DSA`
`POST /dsa/upload-emis  →  DsaController.uploadDsaEmis  (src/routes/dsa.route.ts)  — Upload DSA EMI file`
`GET /dsa/mis-report  →  DsaController.getMisReport  (src/routes/dsa.route.ts)  — DSA MIS report`
`GET /dsa/download-mis  →  DsaController.downloadMisReport  (src/routes/dsa.route.ts)  — Download MIS report`

### Filter
`POST /filter  →  FilterController.getFilter  (src/routes/filter.route.ts)  — Get filter options for a page`

### App Function
`GET /app-function/holiday-list  →  AppFunctionController.getHolidayList  (src/routes/appFunction.route.ts)  — Get repay date holidays`
`POST /app-function/add-holiday  →  AppFunctionController.addHolidayList  (src/routes/appFunction.route.ts)  — Add holiday`
`DELETE /app-function/delete-holiday  →  AppFunctionController.deleteHolidayList  (src/routes/appFunction.route.ts)  — Delete holiday`
`GET /app-function/disb-status  →  AppFunctionController.getDisbStatus  (src/routes/appFunction.route.ts)  — Get auto-disb status`
`PUT /app-function/disb-status  →  AppFunctionController.updateDisbStatus  (src/routes/appFunction.route.ts)  — Update auto-disb status`
`GET /app-function/gateway-type  →  AppFunctionController.getGatewayType  (src/routes/appFunction.route.ts)  — Get repayment gateway type`
`PUT /app-function/gateway-type  →  AppFunctionController.updateRepaymentGatewayType  (src/routes/appFunction.route.ts)  — Update gateway type`

### Contact Us
`POST /contact-us  →  ContactUsController.contactExcelData  (src/routes/contactUs.route.ts)  — Export contact-us data`

### Deep Link
`GET /deeplink  →  DeepLinkController.redirect  (src/routes/deeplink.route.ts)  — Deep-link redirect (device detection)`

### User Management
`GET /user  →  UserController.getManagementUserList  (src/routes/user.route.ts)  — List management users`
`POST /user  →  UserController.managementUserListAdd  (src/routes/user.route.ts)  — Add management user`
`PUT /user  →  UserController.managementUserListEdit  (src/routes/user.route.ts)  — Edit management user`
`GET /user/login-logs  →  UserController.getManagementLoginLogs  (src/routes/user.route.ts)  — Login logs`
`GET /user/report-access  →  UserController.getManagementReportAccess  (src/routes/user.route.ts)  — Report access`
`PUT /user/report-access  →  UserController.updateManagementReportAccess  (src/routes/user.route.ts)  — Update report access`
`GET /user/whitelist-ip  →  UserController.getWhitelistIPs  (src/routes/user.route.ts)  — Whitelist IPs`
`POST /user/whitelist-ip  →  UserController.addWhitelistIP  (src/routes/user.route.ts)  — Add whitelist IP`
`DELETE /user/whitelist-ip  →  UserController.deleteWhitelistIP  (src/routes/user.route.ts)  — Delete whitelist IP`
`GET /user/roles  →  UserController.getRolesList  (src/routes/user.route.ts)  — List roles`
`POST /user/roles  →  UserController.addRoleDetails  (src/routes/user.route.ts)  — Add role`
`PUT /user/roles  →  UserController.updateRoleDetails  (src/routes/user.route.ts)  — Update role`
`GET /user/roles/:id  →  UserController.getRoleDetails  (src/routes/user.route.ts)  — Get role detail`
`GET /user/permissions  →  UserController.getPermissionsList  (src/routes/user.route.ts)  — List permissions`
`POST /user/permissions  →  UserController.addPermissionDetails  (src/routes/user.route.ts)  — Add permission`
`PUT /user/permissions  →  UserController.updatePermissionDetails  (src/routes/user.route.ts)  — Update permission`
`GET /user/permissions/:id  →  UserController.getPermissionDetails  (src/routes/user.route.ts)  — Get permission detail`
`GET /user/role-permissions/:id  →  UserController.getRoleHavePermissions  (src/routes/user.route.ts)  — Get permissions for role`
`PUT /user/role-permissions/:id  →  UserController.updateBulkRoleHavePermissions  (src/routes/user.route.ts)  — Bulk update role permissions`
`GET /user/dashboard  →  UserController.dashboard  (src/routes/user.route.ts)  — CRM dashboard metrics`
`GET /user/excel  →  UserController.downloadExcelUserList  (src/routes/user.route.ts)  — Download user list Excel`

### Common
`POST /common/experian-user  →  CommonController.experianUserDetails  (src/routes/common.route.ts)  — Experian user details`
`POST /common/experian-crm  →  CommonController.experianCrmDetails  (src/routes/common.route.ts)  — Experian CRM details`
`POST /common/experian-bureau  →  CommonController.experianBureauDetails  (src/routes/common.route.ts)  — Experian bureau details`
`POST /common/stepper  →  CommonController.stepper  (src/routes/common.route.ts)  — Get/set onboarding stepper`
`PUT /common/data-update  →  CommonController.dataUpdate  (src/routes/common.route.ts)  — Generic table data update`

### Lentra Report
`POST /lentra-report/failed-loans  →  LentraReportController.getFailedLoanReport  (src/routes/lentraReport.route.ts)  — Lentra failed loan report`
`GET /lentra-report/failed-loans/export  →  LentraReportController.exportFailedLoanReport  (src/routes/lentraReport.route.ts)  — Export Lentra failed loans`

### Index
`GET /  →  IndexController.index  (src/routes/index.route.ts)  — Health check / root`

---

## DATA_MODELS
### MySQL (Knex models in `src/database/mysql/`)

`IAddress  (src/interfaces/address.interface.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy  — relationships: customer`

`IApiReqResLog  (src/interfaces/api_req_res_log.interface.ts)  — fields: id, customerID, mobile, api_request, api_response, created_at, status, message, api_name`

`IAppInstallationsLog  (src/interfaces/app_installations.interface.ts)  — fields: id, apps, customerID, created_at, iu_date, updated_at`

`IApproval  (src/interfaces/approval.interface.ts)  — fields: approvalID, customerID, leadID, loanType, productType, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, plateFormFee, convinineceFee, creditRiskAnalisys, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, activeLoans, activePL, activeHL, activeCC, activePaydayLoan, outstandingAmount, monthlyObligation, status, formNo, employed, remark, loanRequirePurpose, creditedBy, rejectionReason, documentr, redFlag, createdDate, sanctionalloUID, customerApproval, employmentType, m1-m3, m_avg, p1-p3, m1_date-m3_date, disbursalRemark  — relationships: customer, lead`

`IAppVideoModel  (src/interfaces/appVideo.interface.ts)  — fields: vid, customerID, leadID, vSize, viFile, vUrl, credated_date, upload_platform, rejected_status`

`IAutoDisbStatus  (src/interfaces/auto_disb_status.interface.ts)  — fields: id, auto_disb_status`

`IAutoDisbStatusLog  (src/interfaces/auto_disb_status_log.interface.ts)  — fields: changed_status, changed_by`

`IAutoDisbursalLogsModel  (src/interfaces/auto_disbursal_logs.interface.ts)  — fields: id, customerID, leadID, api_request, api_response, userID, any_error, status, createdDate`

`IBankUpdateCheckModel  (src/interfaces/bank_update_check.interface.ts)  — fields: id, customerID, leadID, data`

`IBankIfscModel  (src/interfaces/bankIfsc.interface.ts)  — fields: id, BANK, IFSC, BRANCH, CENTRE, DISTRICT, STATE, ADDRESS, CONTACT, IMPS, RTGS, CITY, ISO3166, NEFT, MICR, UPI, SWIFT, is_active`

`ICustomerBlackListModel  (src/interfaces/blackListCustomer.interface.ts)  — fields: id, customerid, leadid, email, mobile, date, uid, lead_status, message, iu_date`

`IBlacklistCustomerPancard  (src/interfaces/blackListCustomerPancard.interface.ts)  — fields: id, pancard, status, addBy, addDate, removeBy, removeDate, createdDate, reason`

`ICallDisposition  (src/interfaces/callDisposition.interface.ts)  — fields: id, call_date, call_time, loan_no, agent_name, campaign, disposition, sub_disposition, callback_time, next_action_datetime, ptp_amount, remarks, lot_name, branch_name, customer_name, customer_email, customer_mobile, loan_amount, due_date_repay_amount, repay_amount, disbursed_date, repay_date, remaining_collection, total_collection, loan_tenure, roi, address, call_landing_time, call_duration, disposition_duration, end_call_time, hangup_by`

`ICallHistoryModel  (src/interfaces/callHistory.interface.ts)  — fields: callHistoryID, customerID, leadID, callType, status, noteli, remark, callbackTime, calledBy, createdDate`

`ICallHistoryLog  (src/interfaces/callhistorylogs.interface.ts)  — fields: callHistoryID, customerID, leadID, callType, status, appAmount, noteli, remark, callbackTime, calledBy, createdDate`

`IChatLog  (src/interfaces/chat_logs.interface.ts)  — fields: id, leadID, agent_id, customer_reply, customer_number, message, messgae_json, status, created_at, api_request, api_response, message_id, msg_seen, document_type, cron_msg_send, iu_date`

`ICollection  (src/interfaces/collection.interface.ts)  — fields: collectionID, customerID, leadID, loanNo, collectedAmount, penaltyAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, createdDate, collectionStatus, collectionStatusby, approvedDate, orderID, excess_amount, discount_waiver, discount_waiver_amount, refund_utr_no, opening_balance, closing_balance, total_interest, principal_amount, penality_charge, collected_interest, collected_principal, collected_penality, updated_date, collectedDateIST, refundType, refundRemarks, approvedBy, amount, mode, remarks  — relationships: customer, lead, loan`

`ICollectionFollowUp  (src/interfaces/collectionFollowUp.interface.ts)  — fields: reviewID, customerID, leadID, loanNo, followType, StatusType, statusTypeDate, remark, createdBy, createdDate, followup_type, reason, iu_date`

`ICreditReport  (src/interfaces/credit_report.interface.ts)  — fields: id, cr_provider, bucket_id, customerID, stage_one_id, stage_two_id, errors, status, score, response_time, initiated_by, action_type, cb_mark, created_by, log_id, created_at, updated_at, updated_by, unique_cust_id`

`ICreditScoreUserJourney  (src/interfaces/credit_socore_user_journey.interface.ts)  — fields: id, step, attempt, customerID`

`ICredit  (src/interfaces/credit.interface.ts)  — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, actualTenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, paneltyEmis, status, principal, amountToBeRepayed, firstDueDate, brokenPeriodIntrest, gst, created_at, disbursalDate  — relationships: customer, lead`

`ICustomer  (src/interfaces/customer.interface.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, dob_digit_match_btn_click, sim_available, emandate_required, email_verification_status, email_delivery_status, email_last_validation, step, ckyc_status`

`ICustomerAccount  (src/interfaces/customerAccount.interface.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, createdDate, bank_holder_name, is_credit, isAadharVerified  — relationships: customer, lead`

`ICustomerApp  (src/interfaces/customerApp.interface.ts)  — fields: customerID, name, firstName, middlename, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, isVerified, employeeType, createdDate, loanRequeried, purposeloan, companyName, companyAddress, monthlyIncome, salaryMode, residenceType, residenceAddress, device, uid, step, state, city, pincode, utmSource, status, lead_status, new_form, remark, bank_name, bank_ifsc, bank_account_no, bank_holder_name, residenceAddress2, landmark, area, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, office_email_id, office_email_otp, is_verified_email, sim_available, dob_digit_match_btn_click, is_pan_aadhar_linked, is_dob_match, email_verification_status, email_delivery_status, email_last_validation`

`ICustomerAppLocation  (src/interfaces/customerAppLocation.interface.ts)  — fields: id, mobile, customerID, residenceAddress, state, city, pincode, created_at`

`ICustomerDnd  (src/interfaces/customerDnd.interface.ts)  — fields: id, name, customerID, mobile, reason, start_date, expiry_date, created_at, updated_at, pancard, updated_by, is_deleted, removed_by, updatedName, removedName`

`ICustomerHistory  (src/interfaces/customerHistory.interface.ts)  — fields: id, customerID, changedBy, changeType, tableName, fieldName, oldValue, newValue, changeReason, ipAddress, userAgent, createdAt`

`ICustomerSalary  (src/interfaces/customerSalary.interface.ts)  — fields: id, customerID, salary_date, particulars, amount, createdBy, created_at`

`IDialerLog  (src/interfaces/dialer_logs.interface.ts)  — fields: id, lead_id, mobile_no, user_id, api_type, api_trace_id, api_message, api_status, api_response, created_at, src, customer_no, call_start_time, call_end_time, agent_ring_time, agent_talk_time, call_status, hangup_cause, hangup_text, unique_id, callback_created_at, iu_date`

`IDisbursalJobsModel  (src/interfaces/disbursalJobs.interface.ts)  — fields: id, customerID, leadID, loanID, loanNo, accountNo, ifsc, actualDisbAmount, custName, custMobile, custEmail, companyAcc, userID, createdDate, currentStatus, jobStatus, apiStatus`

`IDocument  (src/interfaces/document.interface.ts)  — fields: documentID, customerID, leadID, documentType, documentFile, password, status, verifiedBy, verifiedDate, uploadBy, uploadedDate, type, upload_platform, iu_date`

`IDocumentFinbox  (src/interfaces/documentFinbox.interface.ts)  — fields: documentID, customerID, leadID, entityID, type, statement_id, documentType, documentFile, verifiedBy, status, verifiedDate, uid, aa_check, iu_date`

`IDsa  (src/interfaces/dsa.interface.ts)  — fields: id, dsa_name, min_age, max_age, employment, min_salary, min_income_se, geography, credit_score, min_loan_amount, max_loan_amount, tenure_min_months, tenure_max_months, pf_starting, interest_starting, is_deleted, created_at, updated_at`

`IEmandateNotRequiredLogsModel  (src/interfaces/emandate_not_required_logs.interface.ts)  — fields: id, customerID, nr_startBy, nr_startDate, nr_endBy, nr_endDate, last_emandate_paid`

`IEmi  (src/interfaces/emi.interface.ts)  — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paneltyID, paymentID, status, amountRemains, createdAt, updatedAt, amountRemainsInterest, amountRemainsPenalty, amountRemainsBrokenPeriodIntrest, brokenPeriodIntrest, accessAmount, color, bgcolor, paymentReceived, is_deleted, waive_off_amount  — relationships: credit, lead`

`IEMITransaction  (src/interfaces/emiTransactions.interface.ts)  — fields: transaction_id, order_id, emi_id, interest, principal, penalty, dpd_amount, transaction_date, lead_id, emi_status`

`IEmployer  (src/interfaces/employer.interface.ts)  — fields: employerID, customerID, leadID, employerName, empEmail, empDob, empSalary, empDesignation, empWorkIndustry, employment, totalExperience, currentCompany, address, city, state, pincode, status, verifiedBy, createdDate, office_email_id, office_email_otp, is_verified_email`

`IFinboxClientUrl  (src/interfaces/finboxClientUrl.interface.ts)  — fields: id, leadID, customerID, url, uid, credated_date`

`IKalyeraLog (MySQL)  (src/interfaces/kaleyralogs.interface.ts)  — fields: id, leadID, customerID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, mobile_no, pancard, aadharNo, code, state, entity_id, sync_id, sync_result, sync_data, amount`

`ILeadsApiLog  (src/interfaces/lead_api_log.interface.ts)  — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo, code, state, entity_id, sync_id, sync_result, sync_data, amount`

`ILead  (src/interfaces/lead.interface.ts)  — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, commingLeadsDate, ip, callAssign, creditAssign, createdDate, alloUID, sanctionalloUID, sanctionAppID, entity_id, field_officer_id, field_officer_assign_date, field_officer_lead_status, em_id, step, kfs, bureauVersion, bankingSurrogateVersion, MLresponse, MLfeatures, MLamount, MLsalary, mlDateTime, productID, ipc, hold_date, hold_time, iu_date, lenderID, kfs_ip  — relationships: customer`

`ILentraCustomerMapping  (src/interfaces/lentra.interface.ts)  — fields: id, customerID, leadID, lms_id, los_id, loan_no, entity_id, bank_details_id, created_at, updated_at, isNachNeeded, nachMandateId, nachStatus, stpStatus, mandateCanceled, workflow_id, reference_id, stp_retries, nach_retries, nach_cancel_retries`

`ILoan  (src/interfaces/loan.interface.ts)  — fields: loanID, leadID, lenderID, loanNo, customerID, approvalID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, accountNo, accountType, bankIfsc, bank, bankBranch, chequeDetails, pdDate, pdDoneBy, repayDate, deduction, remarks, status, rejReason, companyAccountNo, ip, disbursedBy, createdDate, allocate_date, allocated_by, is_manual, manual_date, utr, payout_status, cooling_period_flag, cooling_period_date  — relationships: customer, lead, approval`

`ILoginLogs  (src/interfaces/loginLogs.interface.ts)  — fields: id, userID, name, email, ip, loginStart, loginEnd, iu_date`

`IMailTemplate  (src/interfaces/mail_template.interface.ts)  — fields: id, name, subject, message`

`IMobileDecryptionLog  (src/interfaces/mobile_decryption_log.interface.ts)  — fields: id, user_id, decrypted_mobile, created_at, updated_at`

`IMobileToken  (src/interfaces/mobileToken.interface.ts)  — fields: id, customerID, mobile, appID, credatedDate, imei, access_token, last_login, android_id, firebase_token, jwt_access_token`

`INotification  (src/interfaces/notification.interface.ts)  — fields: notificationID, customerID, leadID, notification, type, subject, createdDate, mtype, uid`

`INoLoanFollowUpLogs  (src/interfaces/lead.interface.ts)  — fields: id, lead_id, customer_id, follow_up_by, follow_type, status_type, remark, created_at, updated_at, iu_date`

`IOnlinePayment  (src/interfaces/onlinepayment.interface.ts)  — fields: pID, name, email, phone, service, typeProduct, toValue, message, razorpayOrderId, razorpayPaymentId, paymentStatus, makerstamp, updatestamp, status, approved_id, paymentType, method, leadID, device`

`IOnlinePaymentLog  (src/interfaces/onlinepaymentlog.interface.ts)  — fields: id, pID, razorpayOrderId, razorpayPaymentId, paymentStatus, createdDate`

`IOtherCharges  (src/interfaces/other_charges.interface.ts)  — fields: id, emiID, creditID, amount, customerID, transectionID, discription, status, leadID, loanID`

`IPaymentModeForBanks  (src/interfaces/payment_mode_for_banks.interface.ts)  — fields: id, bank_name, payment_mode, created_by, created_date, updated_by, updated_date, status, id_date`

`IPaymentMode  (src/interfaces/payment_mode.interface.ts)  — fields: id, mode, status, id_date`

`IPennyDropModel  (src/interfaces/pennyDrop.interface.ts)  — fields: id, customerID, p_id, leadID, name, ifsc, bank_name, account_number, account_status, registered_name, credated_date, logs, penny_status, uid, penny_drop_name_match, penny_type`

`IPermission  (src/interfaces/permissions.interface.ts)  — fields: permission_id, permission_name, permission_display_name, permission_type, status, created_by, created_at, updated_at, updated_by`

`IProduct  (src/interfaces/product.interface.ts)  — fields: productID, name, logo, discription, type, step, status, leadID, customerID`

`IRazorpayEMOrder  (src/interfaces/razorpay_emOrder.ts)  — fields: id, emID, customerID, leadID, orderID, entity, amount, amount_paid, amount_due, currency, receipt, remarks, status, notes_key_1, razorpay_payment_id, razorpay_order_id, razorpay_signature, tokenID, uid, createdDate`

`IRazorpayLog  (src/interfaces/razorpay_logs.interface.ts)  — fields: id, customerID, leadID, req_url, api_request, api_response, type, created_at`

`IRazorPayMandateStatusModel  (src/interfaces/razorpay_mandate_status.interface.ts)  — fields: id, emId, leadID, customer_id, inv_id, emstatus, credated_date, tokenID, accountNo, accountType, bank, ifsc`

`IRazorpayMandate  (src/interfaces/razorpay_mandate.interface.ts)  — fields: id, customerID, accountNo, accountType, bank, ifsc, leadID, inv_id, entity, receipt, invoice_number, customer_id, cust_name, cust_email, cust_contact, order_id, status, sms_status, email_status, short_url, type, credated_date, uid, devices, etype, token_id, emMaxamount, res_response, need_another_mandate, name_missmatch_reject, payment_id`

`IRazorPayPayoutAccountsModel  (src/interfaces/razorpay_payout_accounts.interface.ts)  — fields: payaccID, customerID, leadID, acc_id, entity, contact_id, account_type, ifsc, bank_name, name, account_number, active, batch_id, createdDate, uid`

`IRazorPayPayoutContactsModel  (src/interfaces/razorPayPayoutContacts.interface.ts)  — fields: payoutID, customerID, leadID, cont_id, cont_entity, cont_name, cont_contact, cont_email, cont_type, cont_reference_id, cont_batch_id, cont_active, cont_notes_key_1, cont_notes_key_2, createdDate, uid, iu_date`

`IRazorpayPayoutDisbursedAmount  (src/interfaces/razorpay_payout_disbured_amount.interface.ts)  — fields: disID, disbDate, id, entity, fund_account_id, amount, currency, notes_key_1, notes_key_2, fees, tax, status, utr, mode, purpose, reference_id, narration, batch_id, description, source, reason, merchant_id, status_details_id, customerID, leadID, creadatedDate, failure_reason, uid, reamrk, api_log, bank_changed, is_checked`

`IRazorpaySubscription  (src/interfaces/razorpay_subscription.interface.ts)  — fields: id, customerID, startAt, endAt, status, cancelled_date, productID, razorpay_response, razorpay_subscription_id, createdAt, updatedAt`

`IReferenceModel  (src/interfaces/reference.interface.ts)  — fields: referenceID, customerID, relation, name, address, city, state, pincode, contactNo, createdBy, createdDate, name_contact, reference_verify, is_verified, recording, upload_platform`

`IRefundReasons  (src/interfaces/refundReasons.interface.ts)  — fields: reasonID, reason, isActive`

`IRepayDateHolidayModel  (src/interfaces/repayDateHoliday.interface.ts)  — fields: id, repaydate`

`IRepaymentGatewayTypeModel  (src/interfaces/repayment_gateway_type.interface.ts)  — fields: id, gateway_type, hard_status, created_at, updated_at, some_other_field`

`IReportLog  (src/interfaces/reportLog.interface.ts)  — fields: id, user_id, user_name, report_name, requested_url, requested_params, ip_address, created_at, updated_at`

`IRole  (src/interfaces/roles.interface.ts)  — fields: role_id, role_name, role_display_name, status, created_at, created_by, updated_at, updated_by`

`IRolePermissionLinks  (src/interfaces/role_permission_links.interface.ts)  — fields: id, role_id, permission_id, status, created_at, created_by, updated_at, updated_by, iu_date`

`ISendInblueLog  (src/interfaces/send_inblue_log.interface.ts)  — fields: id, created_at, customer_id, iu_date, api_response, type, updated_at`

`ISourcePartner  (src/interfaces/sourcePartner.interface.ts)  — fields: id, image, name, link, status, created_at, updated_at`

`IState  (src/interfaces/states.interface.ts)  — fields: stateID, stateName, status, createdDate, code, cibil_state_code`

`IStepControlModel  (src/interfaces/step-control.interface.ts)  — fields: id, product_id, provider_id, instrument_id, step_name, step_display_name, pre_step_name, pre_step_display_name, post_step_name, post_step_display_name, step_order, next_route, is_active, created_at, created_by, updated_by, updated_at, current_route, prev_route, dashboard_message1-4, should_recheck`

`IStepTrackerModel  (src/interfaces/step-tracker.interface.ts)  — fields: id, step_id, is_completed, created_at, updated_at, is_skippable, customer_id, lead_id  — relationships: step_control`

`ISubscriptionPayment  (src/interfaces/subscription_payments.interface.ts)  — fields: id, customerID, subscriptionId, orderId, paymentId, amount, gst, totalAmount, status, response, createdAt, updatedAt`

`ISubscriptionRefund  (src/interfaces/subscription_refunds.interface.ts)  — fields: id, pg_refund_id, amount, payment_id, status, subscriptionId, customerID, createdAt, updatedAt`

`ITransection  (src/interfaces/transections.interface.ts)  — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, deleted, gateway, createdAt, updatedAt, createdBy, updatedBy, amount, collectionID, emiID, transactionDate, remarks, payment_transaction_status, waiver, discount_type`

`IUserLoginAttempt  (src/interfaces/user_login_attempts.interface.ts)  — fields: userID, login_attempt, otp_attempt, last_attempt`

`IUserMetadata  (src/interfaces/user_metadata.interface.ts)  — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image, created_at, updated_at`

`IUserSummary  (src/interfaces/user_summary.interface.ts)  — fields: id, api_type, customerID, provider_id, json_value, Status, created_at, created_by, updatedAt`

`IUser (management)  (src/interfaces/users.interface.ts)  — fields: userID, name, email, mobile, did_no, branch, userName, password, role, status, createdBy, createdDate, accessPer, utype, firebase_token, device_token, lip, convoque_login_id, convoque_exten, whatsapp_email, lead_status, otp, password_updated_at, mac_address, random_id, mac_otp, utmSource`

`IWhitelistIP  (src/interfaces/users.interface.ts)  — fields: id, ip, status, added_by`

`IVirtualAccount  (src/interfaces/virtualAccount.interface.ts)  — fields: accID, customerID, leadID, accounID, name, customer_id, recid, entity, ifsc, bankName, recName, account_number, credatedDate, uid, iu_date`

`IWhatsappDisposition  (src/interfaces/whatsapp_disposition.interface.ts)  — fields: id, phone_number, country_code, customer_name, failed, failure_reason, sent_timestamp, delivered_timestamp, read_timestamp, replied_timestamp, campaign_owner_email, loan_no`

`IWhatsappLog  (src/interfaces/whatsapp_log.interface.ts)  — fields: id, customer_id, id_date, response, type, updated_at, created_at`

`IWhatsappMessageIds  (src/interfaces/whatsapp_message_ids.interface.ts)  — fields: id, wc_id, template_name, leadID, lead_status, send_from, user_id, created_at, updated_at, iu_date`

`IReportAccess  (src/interfaces/reports.interface.ts)  — fields: id, name, procedure, input, created_at, updated_at, delete, date`

`IReportPermissionSchema  (src/interfaces/reports.interface.ts)  — fields: permissionId, reportId, userId, view, download`

### Prisma / MySQL (schema.prisma)
`User  (src/database/prisma/schema.prisma)  — fields: id (Int, PK autoincrement), email (String unique), password (String)`

### MongoDB (Mongoose models in `src/database/mongo/model/`)

`CustomerAssetData  (src/database/mongo/model/CustomerAssetData.ts)  — fields: userId, leadId, shakey, customerAsset  — relationships: none`

`EmiAutoPaymentCronLog  (src/database/mongo/model/EmiAutoPaymentCronLog.ts)  — fields: emiIDs (number[]), individualRecord (IIndividualRecord[]), createdAt, updatedAt  — relationships: none`

`KaleyraLogs  (src/database/mongo/model/KaleyraLogs.ts)  — fields: mobile, req_url, api_request, api_response, curl_error, type, created_at`

`RazorpayRefundLogs  (src/database/mongo/model/RazorpayRefundLogs.ts)  — fields: leadID, customerID, loanNo, refund_id, payment_id, order_id, refund_amount, excess_amount, status, refund_mode, reason, product_id, fileName, folderName, utr, created_at, processed_at, uid, name, mobile, email, pancard`

`RazorpayWebhookLogs  (src/database/mongo/model/RazorpayWeebhookLogs.ts)  — fields: id (ObjectId), subscriptionId, response, createdAt, updatedAt`

`User (Mongo)  (src/database/mongo/model/User.ts)  — fields: name, email, password`

`LentraLogs  (src/models/lentraLogs.model.ts)  — fields: apiRequest, apiResponse, apiType, customerID, leadID, createdAt, updatedAt  — (Mongoose model, schema defined in model file)`

### Redis (ioredis / Bull)
`Queue (Bull)  (src/queues/createQueue.ts)  — Bull job queue; fields: name, attempts, removeOnComplete, backoff  — used for background job processing`
