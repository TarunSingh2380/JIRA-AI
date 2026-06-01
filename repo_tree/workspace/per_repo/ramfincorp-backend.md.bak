## ARCHITECTURE
**Entry Point:** `src/server.ts` → instantiates `App` class (`src/app.ts`) with all route modules → Express HTTP server on configurable port (default 8080).

**Top-Level Modules:**
- `src/app.ts` — Express app bootstrap: middleware, routes, Swagger, cron jobs, MongoDB/MySQL connections; graceful shutdown on SIGINT/SIGTERM/uncaughtException (destroys Knex pool, force-exits after 5s timeout)
- `src/config.server.ts` — Config loading from env vars + defaults
- `src/routes/index.ts` — Aggregates all route classes
- `src/controllers/` — Request handlers (30+ controllers)
- `src/services/` — Business logic layer (60+ services)
- `src/database/` — Data access: `mongo/` (Mongoose models/repos), `mysql/` (Knex-based models), `prisma/` (unused/minimal)
- `src/middlewares/` — Auth, error handling, validation, step-checking, event logging
- `src/consumers/` — SQS/Kafka message consumers
- `src/producers/` — SQS message producers
- `src/workers/` — Worker thread wrappers
- `src/services/cronJobs/` — Scheduled cron jobs
- `src/utils/pushAdhar.ts` — Utility to backfill Aadhaar numbers into user_metadata from leads_api_log in batches

**External Services:**
- **MySQL** (via Knex) — primary relational store (customers, loans, EMIs, leads, approvals, etc.); connection pool with auto-reconnect (max 4 attempts, pool listeners for createFail/acquireFail)
- **MongoDB** (via Mongoose) — logs, event logs, webhook logs, Kaleyra logs, Lentra logs
- **Redis** (via ioredis) — caching, OTP storage, LMS flow decisions, queues (Bull), distributed lock for retryStpCron
- **AWS S3** — document/file storage
- **AWS SQS** — async job queues (Razorpay webhook settlement, missing payment, disbursal documents, Lentra STP)
- **Kafka** (KafkaJS) — Razorpay payment event consumption
- **Razorpay** — payment gateway (penny drop, e-mandate, repayments, payouts)
- **PayU** — alternative payment gateway
- **Firebase** — push notifications
- **Decentro** — bank account validation, Aadhaar/DigiLocker KYC
- **SurePass** — PAN/Aadhaar OTP verification
- **Digitap** — face liveness, PAN verification
- **Finbox** — bank statement analysis
- **HyperVerge** — onboarding/KYC
- **Lentra LMS** — external loan management system integration (STP, NACH, repayment webhook, fund-in, statement of accounts, due transaction details)
- **CIBIL/Experian/Bureau** — credit bureau APIs
- **Kaleyra/MSG91/TextNation/Acquirit** — SMS/OTP providers
- **AWS SES / Brevo (SendinBlue)** — email delivery
- **WebEngage** — marketing analytics

**Core Request Lifecycle:** Client → Express middleware (auth, validation, step-check) → Controller → Service → DB model → Response

---

## ROUTES
### Index
`GET /`  →  IndexController (src/routes/index.route.ts)

### Bureau Decision (`/api/v1/ramfincorp`)
`GET /api/v1/ramfincorp/health`  →  BureauDecisionController.healthCheck  (src/routes/bureauDecision.route.ts)  — Health check
`POST /api/v1/ramfincorp/bureau-decision`  →  BureauDecisionController.processBureauDecision  (src/routes/bureauDecision.route.ts)  — Process bureau decision with API key auth
`POST /api/v1/ramfincorp/dsa-pan-verification`  →  BureauDecisionController.processDsaPanVerification  (src/routes/bureauDecision.route.ts)  — DSA PAN verification
`POST /api/v1/ramfincorp/check-lead-status`  →  BureauDecisionController.checkLeadStatus  (src/routes/bureauDecision.route.ts)  — Check lead status by mobile

### CIBIL Score (`/cibil`)
`GET /cibil/terms-and-conditions`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Get T&C
`POST /cibil/update-journey`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Update user journey step
`POST /cibil/create-checkout`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Create Razorpay subscription checkout
`GET /cibil/payment-status`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Get subscription payment status
`POST /cibil/experian-pull`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Pull Experian credit report
`POST /cibil/answer-questions`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Submit Experian auth questions
`POST /cibil/payment-checkout`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Process subscription payment
`GET /cibil/journey-step`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Get current journey step
`GET /cibil/subscriptions`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — List subscriptions
`GET /cibil/subscription-payments`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — List subscription payments
`GET /cibil/subscription-process`  →  CibilScoreController (src/routes/cibilscore.route.ts)  — Get subscription process
`POST /cibil/report-summary`  →  CibilScoreController.reportSummary  (src/routes/cibilscore.route.ts)  — Get credit report summary
`POST /cibil/account-details`  →  CibilScoreController.accountDetails  (src/routes/cibilscore.route.ts)  — Get account details
`POST /cibil/view-impact`  →  CibilScoreController.viewImpactDetails  (src/routes/cibilscore.route.ts)  — View credit impact
`GET /cibil/fetch-order-details`  →  CibilScoreController.fetchRazorpayOrder  (src/routes/cibilscore.route.ts)  — Fetch Razorpay order

### Collection CRM (`/collection-crm`)
`POST /collection-crm/add`  →  CollectionCrmController (src/routes/collectionCrm.route.ts)  — Add collection entry
`GET /collection-crm/all`  →  CollectionCrmController (src/routes/collectionCrm.route.ts)  — Get all collections

### Common (`/common`)
`POST /common/ivr-menu-one`  →  CommonController (src/routes/common.route.ts)  — IVR menu 1 handler
`POST /common/ivr-menu-two`  →  CommonController (src/routes/common.route.ts)  — IVR menu 2 handler
`POST /common/customer-details`  →  CommonController (src/routes/common.route.ts)  — Get customer details
`GET /common/bank-details`  →  CommonController (src/routes/common.route.ts)  — Get bank details by IFSC
`GET /common/aadhar-down`  →  CommonController (src/routes/common.route.ts)  — Check Aadhaar service status
`POST /common/adhar-push-script`  →  CommonController.runAdharPushScript  (src/routes/common.route.ts)  — Run Aadhaar backfill script (sister service auth)

### CRM (`/crm`)
`PUT /crm/lead-update`  →  CRMController (src/routes/crm.route.ts)  — Update lead
`POST /crm/emi-calculator`  →  CRMController (src/routes/crm.route.ts)  — Calculate EMI
`POST /crm/credit-details`  →  CRMController (src/routes/crm.route.ts)  — Save credit details
`GET /crm/amount-to-disburse`  →  CRMController (src/routes/crm.route.ts)  — Get disbursable amount
`POST /crm/generate-emi`  →  CRMController (src/routes/crm.route.ts)  — Generate EMI schedule
`POST /crm/update-payment`  →  CRMController (src/routes/crm.route.ts)  — Update payment
`POST /crm/apply-penalty`  →  CRMController (src/routes/crm.route.ts)  — Apply penalty
`GET /crm/emis`  →  CRMController (src/routes/crm.route.ts)  — Get EMIs
`GET /crm/docs-requirements`  →  CRMController (src/routes/crm.route.ts)  — Get document requirements
`GET /crm/emi-loan-details`  →  CRMController (src/routes/crm.route.ts)  — Get EMI loan details
`POST /crm/payday-to-emi`  →  CRMController (src/routes/crm.route.ts)  — Convert payday to EMI
`POST /crm/upload-bulk-mandate`  →  CRMController (src/routes/crm.route.ts)  — Upload bulk mandate CSV
`GET /crm/mandates`  →  CRMController (src/routes/crm.route.ts)  — Get mandates
`GET /crm/mandate-file-url`  →  CRMController (src/routes/crm.route.ts)  — Get mandate file URL
`POST /crm/verify-payment`  →  CRMController (src/routes/crm.route.ts)  — Verify Razorpay payment range
`POST /crm/verify-payu-payment`  →  CRMController (src/routes/crm.route.ts)  — Verify PayU payment range

### Customers (`/customers`)
`POST /customers/login`  →  CustomersController (src/routes/customer.route.ts)  — Customer login / send OTP
`POST /customers/verify-otp`  →  CustomersController (src/routes/customer.route.ts)  — Verify OTP
`GET /customers/dashboard`  →  CustomersController (src/routes/customer.route.ts)  — Customer dashboard data
`POST /customers/incompleteDetailsUpdate`  →  CustomersController (src/routes/customer.route.ts)  — Update incomplete customer details + BRE
`POST /customers/partial-incomplete-update`  →  CustomersController (src/routes/customer.route.ts)  — Partial incomplete details update
`GET /customers/check-repeat-case/:leadID`  →  CustomersController (src/routes/customer.route.ts)  — Check repeat case / one-page reloan
`POST /customers/updateEMIPayment`  →  CustomersController (src/routes/customer.route.ts)  — Update EMI payment (Razorpay)
`POST /customers/updatePayUPayment`  →  CustomersController (src/routes/customer.route.ts)  — Update PayU payment
`GET /customers/emi-soa`  →  CustomersController (src/routes/customer.route.ts)  — EMI statement of account
`GET /customers/one-page-view`  →  CustomersController (src/routes/customer.route.ts)  — One-page loan view
`GET /customers/repayment-page`  →  CustomersController (src/routes/customer.route.ts)  — Repayment page data
`POST /customers/check-pdf`  →  CustomersController (src/routes/customer.route.ts)  — Check/generate PDF
`GET /customers/loans`  →  CustomersController (src/routes/customer.route.ts)  — Customer loan list
`POST /customers/dsa-lead-creation`  →  CustomersController (src/routes/customer.route.ts)  — DSA lead creation (API key auth)
`POST /customers/create-otp`  →  CustomersController (src/routes/customer.route.ts)  — New OTP creation
`POST /customers/verify-otp-service`  →  CustomersController (src/routes/customer.route.ts)  — New OTP verification
`POST /customers/attributions`  →  CustomersController (src/routes/customer.route.ts)  — Save UTM attributions
`GET /customers/lead-bulk`  →  CustomersController (src/routes/customer.route.ts)  — Bulk lead operations
`POST /customers/update-emi-transactions`  →  CustomersController (src/routes/customer.route.ts)  — Update EMI transactions
`POST /customers/update-payout`  →  CustomersController (src/routes/customer.route.ts)  — Update payout status
`POST /customers/update-lead-status`  →  CustomersController (src/routes/customer.route.ts)  — Update lead status
`POST /customers/update-job-status`  →  CustomersController (src/routes/customer.route.ts)  — Update job status
`GET /customers/auto-login`  →  CustomersController (src/routes/customer.route.ts)  — Auto login via JWT
`POST /customers/send-disbursal-document`  →  CustomersController (src/routes/customer.route.ts)  — Send disbursal document to SQS
`GET /customers/get-journey`  →  CustomersController (src/routes/customer.route.ts)  — Get customer journey
`POST /customers/check-pancard-dpd`  →  CustomersController (src/routes/customer.route.ts)  — Check PAN DPD status

### Customer Bank Account (`/customer-bank-account`)
`GET /customer-bank-account/list`  →  CustomerBankAccountController (src/routes/customerBankAccount.route.ts)  — Get bank account list for emandate
`POST /customer-bank-account/confirm`  →  CustomerBankAccountController (src/routes/customerBankAccount.route.ts)  — Confirm bank account
`POST /customer-bank-account/save`  →  CustomerBankAccountController (src/routes/customerBankAccount.route.ts)  — Save bank details
`GET /customer-bank-account/referrer-list`  →  CustomerBankAccountController (src/routes/customerBankAccount.route.ts)  — Get referrer bank accounts
`POST /customer-bank-account/save-referrer`  →  CustomerBankAccountController (src/routes/customerBankAccount.route.ts)  — Save referrer bank details
`POST /customer-bank-account/confirm-referrer`  →  CustomerBankAccountController (src/routes/customerBankAccount.route.ts)  — Confirm referrer bank account

### Document Dispatch (`/document-dispatch`)
`POST /document-dispatch/init`  →  DocumentDispatchController.init  (src/routes/documentDispatch.route.ts)  — Initialize document dispatch
`POST /document-dispatch/mark-sent`  →  DocumentDispatchController.markSent  (src/routes/documentDispatch.route.ts)  — Mark document as sent
`POST /document-dispatch/error`  →  DocumentDispatchController.markError  (src/routes/documentDispatch.route.ts)  — Mark document dispatch error

### Event Funnel (`/event-funnel`)
`GET /event-funnel/report`  →  EventFunnelController (src/routes/eventFunnel.route.ts)  — Get event funnel report

### Lender (`/lender`)
`POST /lender/credentials`  →  LenderController (src/routes/lender.route.ts)  — Add lender credentials
`PUT /lender/credentials`  →  LenderController (src/routes/lender.route.ts)  — Update lender credentials
`GET /lender/credentials`  →  LenderController (src/routes/lender.route.ts)  — Get lender credentials

### Lentra (`/lentra`)
`POST /lentra/stp`  →  LentraController.stp  (src/routes/lentra.route.ts)  — Lentra STP (straight-through processing); on success, triggers disbursal document send via CRM API
`GET /lentra/repayment-page`  →  LentraController.getRepaymentPageData  (src/routes/lentra.route.ts)  — Lentra repayment page data
`GET /lentra/repayment-data`  →  LentraController.getRepaymentData  (src/routes/lentra.route.ts)  — Lentra repayment data
`GET /lentra/retry-stp-cron`  →  LentraController.retryStpCron  (src/routes/lentra.route.ts)  — Manually trigger STP retry cron (sister service auth)
`POST /lentra/fund-in`  →  LentraController.paymentFundIn  (src/routes/lentra.route.ts)  — Initiate Lentra fund-in payment (JWT auth)
`GET /lentra/repayment-fallback`  →  LentraController.lentraRepaymentFallback  (src/routes/lentra.route.ts)  — Lentra repayment fallback check (JWT auth)

### Loan Restructure (`/loan-restructure`)
`GET /loan-restructure/charges/:leadID`  →  LoanRestructureController (src/routes/loanRestructure.route.ts)  — Get restructure charges
`POST /loan-restructure/reason`  →  LoanRestructureController (src/routes/loanRestructure.route.ts)  — Submit restructure reason
`POST /loan-restructure/kfs`  →  LoanRestructureController (src/routes/loanRestructure.route.ts)  — KFS acceptance for restructure
`GET /loan-restructure/kfs-view`  →  LoanRestructureController (src/routes/loanRestructure.route.ts)  — View restructure KFS

### Logs (`/logs`)
`PUT /logs/sms`  →  LogsController.updateSMSLogs  (src/routes/logs.routes.ts)  — Update SMS delivery logs

### Customer Onboarding (`/customer_onboarding`)
`POST /customer_onboarding/pan-verification`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — PAN verification (SurePass/Digitap)
`POST /customer_onboarding/pan-confirmation`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — PAN confirmation
`POST /customer_onboarding/aadhar-otp-send`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Send Aadhaar OTP (SurePass)
`POST /customer_onboarding/aadhar-otp-verify`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Verify Aadhaar OTP (SurePass)
`POST /customer_onboarding/aadhar-verification-initiate-digilocker`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Initiate DigiLocker Aadhaar
`GET /customer_onboarding/aadhar-verification-webhook-digilocker`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — DigiLocker webhook callback
`POST /customer_onboarding/name-email`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Save name and email
`POST /customer_onboarding/email`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Update email
`POST /customer_onboarding/selfie-verification`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Selfie liveness verification
`POST /customer_onboarding/hyperverge-onboard`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — HyperVerge onboarding start
`POST /customer_onboarding/hyperverge-result`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — HyperVerge result fetch
`POST /customer_onboarding/finbox-create-url`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Create Finbox bank connect URL
`POST /customer_onboarding/finbox-bank-connect`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Finbox bank connect callback
`POST /customer_onboarding/penny-drop-initiate`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Initiate penny drop
`POST /customer_onboarding/emandate`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Create emandate
`POST /customer_onboarding/emandate-callback`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Emandate Razorpay callback
`POST /customer_onboarding/reference-details`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Save reference details
`PUT /customer_onboarding/reference-details`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Update reference details
`GET /customer_onboarding/states`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Get state suggestions
`GET /customer_onboarding/approval-view`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Approval view data
`GET /customer_onboarding/approval-view-v2`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Approval view v2 (routes to v3 for Lentra leads)
`POST /customer_onboarding/key-fact`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Generate KFS document (uses Lentra KFS for Lentra leads)
`POST /customer_onboarding/key-fact-acceptance`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Accept KFS
`POST /customer_onboarding/send-kfs`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Send KFS document
`GET /customer_onboarding/fetch-credit-score`  →  CustomerOnboardingController (src/routes/onboarding.routes.ts)  — Fetch credit score

### Page Instruction (`/page-instruction`)
`GET /page-instruction`  →  PageInstructionController (src/routes/pageInstruction.route.ts)  — Get page instruction by name
`POST /page-instruction`  →  PageInstructionController (src/routes/pageInstruction.route.ts)  — Add page instruction

### Payment (`/payment`)
`POST /payment/initiate`  →  PaymentController (src/routes/payment.route.ts)  — Initiate payment (PayU/Razorpay)
`POST /payment/verify-payu`  →  PaymentController (src/routes/payment.route.ts)  — Verify PayU payment response
`POST /payment/verify-razorpay`  →  PaymentController (src/routes/payment.route.ts)  — Verify Razorpay payment

### Referral (`/referral`)
`POST /referral/create`  →  ReferralController.createAndGenerateReferrer  (src/routes/referral.route.ts)  — Create referral link
`GET /referral/url`  →  ReferralController.getReferrarUrl  (src/routes/referral.route.ts)  — Get referral URL
`GET /referral/invite-status`  →  ReferralController.getInviteStatus  (src/routes/referral.route.ts)  — Get invite status list
`GET /referral/invite-status/:id`  →  ReferralController.getInviteStatusById  (src/routes/referral.route.ts)  — Get single invite status
`POST /referral/tracking`  →  ReferralController.tracking  (src/routes/referral.route.ts)  — Track referral

### Report Summary (`/report`)
`GET /report/summary`  →  reportSummary (src/routes/reportSummary.route.ts)  — Credit score report summary
`GET /report/score-history`  →  scoreHistory (src/routes/reportSummary.route.ts)  — Score history

### SMS Delivery Log (`/sms-delivery`)
`POST /sms-delivery/textnation`  →  SmsDelieryLogController (src/routes/smsDelieryLog.route.ts)  — TextNation SMS delivery webhook
`POST /sms-delivery/msg91`  →  SmsDelieryLogController (src/routes/smsDelieryLog.route.ts)  — MSG91 SMS delivery webhook
`POST /sms-delivery/acquirit`  →  SmsDelieryLogController (src/routes/smsDelieryLog.route.ts)  — Acquirit SMS delivery webhook

### SOA (`/soa`)
`POST /soa/generate`  →  SoaController (src/routes/soa.route.ts)  — Generate statement of account PDF
`GET /soa/sanction-data`  →  SoaController (src/routes/soa.route.ts)  — Get sanction data
`GET /soa/sanction-pdf`  →  SoaController (src/routes/soa.route.ts)  — Generate sanction PDF

### Step (`/step`)
`GET /step/next`  →  StepController (src/routes/step.route.ts)  — Get user's next onboarding step
`GET /step/referrer-next`  →  StepController (src/routes/step.route.ts)  — Get referrer next step

### Webhooks (`/webhooks`)
`POST /webhooks/razorpay`  →  WebhookController (src/routes/webhooks.routes.ts)  — Razorpay payment webhook
`POST /webhooks/emandate`  →  WebhookController (src/routes/webhooks.routes.ts)  — Razorpay emandate webhook
`POST /webhooks/decentro`  →  WebhookController (src/routes/webhooks.routes.ts)  — Decentro reverse penny webhook
`POST /webhook/lentra/lentra-repayment-webhook`  →  WebhookController.lentraRepaymentWebhook  (src/routes/webhooks.routes.ts)  — Lentra repayment webhook (Basic auth with lentraWebhookKey/Secret)

### WhatsApp (`/whatsapp`)
`POST /whatsapp/identify`  →  WhatsAppController (src/routes/whatsApp.route.ts)  — Identify customer via WhatsApp
`POST /whatsapp/verify-pan`  →  WhatsAppController (src/routes/whatsApp.route.ts)  — Verify PAN via WhatsApp
`POST /whatsapp/confirm-pan`  →  WhatsAppController (src/routes/whatsApp.route.ts)  — Confirm PAN via WhatsApp
`POST /whatsapp/customer-type`  →  WhatsAppController (src/routes/whatsApp.route.ts)  — Check customer type
`POST /whatsapp/bre-eligibility`  →  WhatsAppController (src/routes/whatsApp.route.ts)  — Check BRE eligibility

### Withdrawal (`/withdrawal`)
`POST /withdrawal/request`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Process withdrawal request
`GET /withdrawal/eligibility`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Check withdrawal eligibility
`GET /withdrawal/history`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Get withdrawal transaction history
`GET /withdrawal/balance`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Get available balance
`GET /withdrawal/limits`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Get withdrawal limits
`GET /withdrawal/transaction/:transactionId`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Get transaction details
`GET /withdrawal/receipt/:transactionId`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Download PDF receipt
`GET /withdrawal/preview-receipt`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Preview receipt template
`POST /withdrawal/webhook`  →  WithdrawalController (src/routes/withdrawal.routes.ts)  — Handle payment gateway webhook

### SQS Consumers (message handlers)
`SQS queue: razorpaySqsQueueUrl`  →  startSqsConsumer  (src/consumers/razorpay.sqs.consumer.ts)  — Process Razorpay webhook messages from SQS
`SQS queue: missingPaymentSettleQueueUrl`  →  consumerLoop  (src/consumers/missing.payment.settlement.consumer.ts)  — Settle missing normal payments
`SQS queue: emandateMissingPaymentSettleQueueUrl`  →  consumerLoop  (src/consumers/emandate.missing.payment.consumer.ts)  — Settle missing emandate payments

### Cron Jobs (scheduled)
`CronJob`  →  CronJobService.retryLentraStp  (src/services/cronJobs/cronJobs.service.ts)  — Retry failed Lentra STP records every 30 minutes (Redis distributed lock, batch size/concurrency from config)
`CronJob`  →  CronJobService.pushLentraToSQS  (src/services/cronJobs/cronJobs.service.ts)  — Push Lentra STP to SQS queue
`CronJob`  →  CronJobService.autoDisbursalCoverage  (src/services/cronJobs/cronJobs.service.ts)  — Auto-approve repeat customers
`CronJob`  →  CronJobService.fetchEMIPayments  (src/services/cronJobs/cronJobs.service.ts)  — Auto-pay EMIs via emandate
`CronJob`  →  CronJobService.managePaymentCron  (src/services/cronJobs/cronJobs.service.ts)  — Settle pending Razorpay payments
`CronJob`  →  CronJobService.updateLeadStatusAfterCheckCOllection  (src/services/cronJobs/cronJobs.service.ts)  — Update lead statuses post collection
`CronJob`  →  CronJobService.updateLeadStatusAfterCheckCOllectionEmi  (src/services/cronJobs/cronJobs.service.ts)  — Update EMI lead statuses
`CronJob`  →  CronJobService.setReferralRewardsProcessing  (src/services/cronJobs/cronJobs.service.ts)  — Process referral rewards daily 6PM IST
`CronJob`  →  CronJobService.checkHourlyDisbursalThreshold  (src/services/cronJobs/cronJobs.service.ts)  — Alert on disbursal anomalies
`CronJob`  →  CronJobService.requeuePendingDocumentsCron  (src/services/cronJobs/cronJobs.service.ts)  — Requeue pending document dispatches
`CronJob`  →  CronJobService.customerExpiredON30Days  (src/services/cronJobs/cronJobs.service.ts)  — Expire 30-day incomplete leads
`CronJob`  →  CronJobService.checkUtm  (src/services/cronJobs/cronJobs.service.ts)  — Process UTM attribution cleanup
`CronJob`  →  RazorPayPaymentSettlementCronService.razorpayWebhookSettlement  (src/services/cronJobs/razorpayPaymentSettlementCron.ts)  — Razorpay SQS-based payment settlement
`CronJob`  →  EventLogsCronJobervice  (src/services/cronJobs/eventLogsCronJob.service.ts)  — Save KFS-done-non-disbursed events

---

## DATA_MODELS
### MySQL (via Knex)

`ICustomer`  (src/interfaces/customer.interface.ts / src/database/mysql/customer.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, kfs_otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, emandate_required, email_verification_status, email_delivery_status  — table: customers

`ILead`  (src/interfaces/lead.interface.ts / src/database/mysql/leads.ts)  — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, ip, em_id, step, kfs, productID, ipc, lenderID, isRestructure, plateform, lms_type, monthlyIncomeConsent, journey_type, isLmsFlowDecided  — table: leads

`IApproval`  (src/interfaces/approval.interface.ts / src/database/mysql/approval.ts)  — fields: approvalID, customerID, leadID, loanType, productType, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, plateFormFee, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, status, remark, rejectionReason, creditedBy, sanctionalloUID, employmentType, disbursalRemark  — table: approval

`ILoan`  (src/interfaces/loan.interface.ts / src/database/mysql/loan.ts)  — fields: loanID, leadID, loanNo, customerID, disbursalAmount, disbursalDate, accountNo, accountType, bankIfsc, bank, status, utr, payout_status, lentra_push_status  — table: loan

`ICredit`  (src/interfaces/credit.interface.ts / src/database/mysql/credit.ts)  — fields: creditID (optional), customerID, leadID, productID, branch, foir, aqb, roi, tenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, status, principal, amountToBeRepayed, firstDueDate, brokenPeriodIntrest, gst, created_at, disbursalDate  — table: credit

`IEmi`  (src/interfaces/emi.interface.ts / src/database/mysql/emi.ts)  — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paymentID, status, amountRemains, brokenPeriodIntrest, accessAmount, paymentReceived, waive_off_amount, is_deleted  — table: emi

`ICustomerAccount`  (src/interfaces/customerAccount.interface.ts / src/database/mysql/customerAccount.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, createdDate, bank_holder_name, is_credit, isAadharVerified, lentraCustomerBankDetailsId  — table: customerAccount

`IAddress`  (src/interfaces/address.interface.ts / src/database/mysql/address.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy  — table: address

`IEmployer`  (src/interfaces/employer.interface.ts / src/database/mysql/employer.ts)  — fields: employerID, customerID, employerName, empEmail, empDob, empSalary, empDesignation, empWorkIndustry, employment, totalExperience, currentCompany, city, state, pincode, status, office_email_id, is_verified_email  — table: employer

`IRazorpayMandate`  (src/interfaces/razorpay_mandate.interface.ts / src/database/mysql/razorpay_mandate.ts)  — fields: id, customerID, accountNo, accountType, bank, ifsc, leadID, inv_id, entity, receipt, status, short_url, type, uid, etype, token_id, emMaxamount, need_another_mandate, name_missmatch_reject, payment_id  — table: razorpay_mandate

`IPennyDropModel`  (src/interfaces/penny_drop.interface.ts / src/database/mysql/penny_drop.ts)  — fields: id, customerID, p_id, leadID, name, ifsc, bank_name, account_number, account_status, registered_name, credated_date, logs, penny_status, uid, penny_drop_name_match, penny_type  — table: penny_drop

`ITransection`  (src/interfaces/transections.interface.ts / src/database/mysql/transections.ts)  — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, deleted, gateway, amount, collectionID, emiID, transactionDate, remarks, payment_transaction_status, waiver, discount_type  — table: transactions

`ICollection`  (src/interfaces/collection.interface.ts / src/database/mysql/collection.ts)  — fields: collectionID, customerID, leadID, loanNo, collectedAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, collectionStatus, orderID, lenderID  — table: collection

`IOnlinePayment`  (src/interfaces/onlinepayment.interface.ts / src/database/mysql/onlinepayment.ts)  — fields: pID, name, email, phone, service, typeProduct, toValue, message, razorpayOrderId, razorpayPaymentId, paymentStatus, status, paymentType, method, leadID, device  — table: onlinepayment

`ILeadsApiLog`  (src/interfaces/lead_api_log.interface.ts / src/database/mysql/lead_api_log.ts)  — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo, code, state, entity_id  — table: lead_api_log (leads_api_log)

`IApiKey`  (src/interfaces/bureau.interface.ts / src/database/mysql/apiKey.ts)  — fields: id, api_key, client_id, client_name, is_active, rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day, allowed_ips, metadata, blocked_until, blocked_reason, last_used_at  — table: api_keys

`IRateLimit`  (src/interfaces/bureau.interface.ts / src/database/mysql/rateLimit.ts)  — fields: id, api_key, client_id, requests_count, window_start, window_type  — table: rate_limits

`IBureauApiLog`  (src/interfaces/bureau.interface.ts / src/database/mysql/bureauApiLog.ts)  — fields: id, request_id, api_key, client_id, user_id, reference_id, endpoint, method, request_data, response_data, http_status_code, processing_status, processing_time_ms, error_code, error_message, client_ip  — table: bureau_api_logs

`ILentraCustomerMapping`  (src/interfaces/lentra.interface.ts / src/database/mysql/lentra_customer_mappings.ts)  — fields: id, customerID, leadID, lms_id, los_id, loan_no, entity_id, bank_details_id, isNachNeeded, nachMandateId, nachStatus, stpStatus, mandateCanceled, workflow_id, reference_id, stp_retries, nach_retries  — table: lentra_customer_mappings

`IUserMetadata`  (src/interfaces/user_metadata.interface.ts / src/database/mysql/user_metadata.ts)  — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image  — table: user_metadata

`IPageInstructions`  (src/interfaces/pageInstructions.interface.ts / src/database/mysql/pageInstructions.ts)  — fields: id, page_name, instruction, created_at, updated_at  — table: pageInstructions

`IStepTrackerModel`  (src/interfaces/step-tracker.ts / src/database/mysql/step_tracker.ts)  — fields: id, step_id, is_completed, is_skippable, customer_id, lead_id, created_at, updated_at  — table: step_tracker

`IStepControlModel`  (src/interfaces/step-control.interface.ts / src/database/mysql/step-control.ts)  — fields: id, product_id, provider_id, step_name, step_order, next_route, is_active, dashboard_message1-4, should_recheck, referrer_step_order, required_steps  — table: step_control

`IRepayDateHolidayModel`  (src/interfaces/repayDateHoliday.interface.ts / src/database/mysql/repayDateHoliday.ts)  — fields: id, repaydate  — table: repayDateHoliday

`IRestructureLoan`  (src/interfaces/loanRestructure.interface.ts / src/database/mysql/restructure_loan.ts)  — fields: id, parentLeadId, childLeadId, reason, status, loan_type  — table: restructure_loan

`IPayuPaymentsSettledByCron`  (src/interfaces/payuPaymentsSettledByCron.interface.ts / src/database/mysql/payuPaymentsSettledByCron.ts)  — fields: id, transaction_id, status, leadID, createdAt  — table: payu_payments_settled_by_cron

`ISMSLogModel`  (src/interfaces/smsLog.interface.ts / src/database/mysql/smsLog.ts)  — fields: id, message, leadId, customerId, status, type  — table: sms_log

`IShortUrlModel`  (src/interfaces/shortUrl.interface.ts / src/database/mysql/shortUrl.ts)  — fields: id, code, long_url, lead_id, opened, opened_at, expires_at  — table: shortUrl (short_url)

`IEmiProcessingFailureLog`  (src/interfaces/emiProcessingFailureLogs.interface.ts / src/database/mysql/emiProcessingFailureLogs.ts)  — fields: id, order_id, failure_type, error_message, status, created_at  — table: emi_processing_failure_logs

`ICustomerKfsLocation`  (src/interfaces/customer_kfs_location.interface.ts / src/database/mysql/customer_kfs_location.ts)  — fields: id, customerID, leadID, latitude, longitude, city, location_source, location_captured_at  — table: customer_kfs_location

### MongoDB (via Mongoose)

`User`  (src/database/mongo/model/User.ts)  — fields: name, email, password  — collection: users

`CustomerAssetData`  (src/database/mongo/model/CustomerAssetData.ts)  — fields: userId, leadId, shakey, customerAsset  — collection: customerassetdatas

`IDocumentDispatch`  (src/database/mongo/model/documentDispatch.model.ts / src/interfaces/documentDispatch.interface.ts)  — fields: leadId, customerId, documents (agreement/disbursal/kfs with sent/sentAt/error), retryCount, lastError, createdAt, updatedAt  — collection: documentdispatches

`IEmiAutoPaymentCronLog`  (src/database/mongo/model/EmiAutoPaymentCronLog.ts)  — fields: emiIDs, individualRecord (emiID, razorpay_mendate_id, status, errorMessage, step), createdAt, updatedAt  — collection: emiautopaymentcronlogs

`IEventLogs`  (src/database/mongo/model/EventLogs.ts)  — fields: mobile, customerId, leadId, utmSource, userType, requestedFrom, eventName, eventDate, status, ip, createdAt  — collection: eventlogs

`IKalyeraLog`  (src/database/mongo/model/KaleyraLogs.ts)  — fields: mobile, req_url, api_request, api_response, curl_error, type, created_at  — collection: kaleyralogs

`ILentraApiLogs`  (src/database/mongo/model/LentraLogs.ts)  — fields: apiRequest, apiResponse, apiType, customerID, leadID, createdAt, updatedAt  — collection: lentraapilogs

`IRazorpayWebhookLogs`  (src/database/mongo/model/RazorpayWeebhookLogs.ts)  — fields: id, subscriptionId, response, createdAt, updatedAt  — collection: razorpaywebhooklogs

`ITrakierInstallInfo`  (src/database/mongo/model/TrakierInstallInfo.ts)  — fields: partner, evid, eval, ets, crtd, cuid, cname, cphone, cmail, inside  — collection: trakierinstallinfos

### Prisma / MySQL (minimal)

`User`  (src/database/prisma/schema.prisma)  — fields: id (Int PK), email (String unique), password (String)  — table: User
