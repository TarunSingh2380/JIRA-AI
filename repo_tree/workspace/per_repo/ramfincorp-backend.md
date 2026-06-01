## ARCHITECTURE
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

## ROUTES
### Index
`GET /  ->  IndexController  (src/routes/index.route.ts)  — health/root`

### Bureau Decision (`/api/v1/ramfincorp`)
`GET  /api/v1/ramfincorp/health  ->  BureauDecisionController.healthCheck  (src/routes/bureauDecision.route.ts)  — health check`
`POST /api/v1/ramfincorp/bureau-decision  ->  BureauDecisionController.processBureauDecision  (src/routes/bureauDecision.route.ts)  — process bureau decision (API key auth)`
`POST /api/v1/ramfincorp/dsa-pan-verification  ->  BureauDecisionController.processDsaPanVerification  (src/routes/bureauDecision.route.ts)  — DSA PAN verification`
`POST /api/v1/ramfincorp/check-lead-status  ->  BureauDecisionController.checkLeadStatus  (src/routes/bureauDecision.route.ts)  — check lead status by mobile`

### Cibil Score (`/cibil-score` or similar)
`GET  /terms-and-conditions  ->  CibilScoreController.getTermsAndConditions  (src/routes/cibilscore.route.ts)  — get T&C`
`POST /update-journeys  ->  CibilScoreController.updateJourneys  (src/routes/cibilscore.route.ts)  — update credit journey step`
`POST /create-checkout  ->  CibilScoreController.createCheckout  (src/routes/cibilscore.route.ts)  — create Razorpay subscription checkout`
`GET  /payment-status  ->  CibilScoreController.getPaymentStatus  (src/routes/cibilscore.route.ts)  — get subscription payment status`
`POST /experian-pull  ->  CibilScoreController.experianPull  (src/routes/cibilscore.route.ts)  — pull Experian credit report`
`POST /answer-questions  ->  CibilScoreController.answerQuestions  (src/routes/cibilscore.route.ts)  — answer Experian auth questions`
`POST /payment-checkout  ->  CibilScoreController.paymentCheckout  (src/routes/cibilscore.route.ts)  — initiate payment checkout`
`POST /update-subscription-payment  ->  CibilScoreController.updateSubscriptionPayment  (src/routes/cibilscore.route.ts)  — webhook for subscription payment`
`GET  /journey-step  ->  CibilScoreController.getJourneyStep  (src/routes/cibilscore.route.ts)  — get current journey step`
`GET  /subscriptions  ->  CibilScoreController.getSubscription  (src/routes/cibilscore.route.ts)  — list subscriptions`
`GET  /subscription-payments  ->  CibilScoreController.getSubscriptionPayments  (src/routes/cibilscore.route.ts)  — list subscription payments`
`GET  /subscription-process  ->  CibilScoreController.getSubscriptionProcess  (src/routes/cibilscore.route.ts)  — get subscription process steps`
`GET  /report-summary  ->  CibilScoreController.reportSummary  (src/routes/cibilscore.route.ts)  — get credit report summary`
`GET  /account-details  ->  CibilScoreController.accountDetails  (src/routes/cibilscore.route.ts)  — get credit account details`
`GET  /view-impact  ->  CibilScoreController.viewImpactDetails  (src/routes/cibilscore.route.ts)  — view credit impact details`
`GET  /fetch-order-details  ->  CibilScoreController.fetchRazorpayOrder  (src/routes/cibilscore.route.ts)  — fetch Razorpay order details`

### Collection CRM
`POST /collection-crm/add  ->  CollectionCrmController.addCollection  (src/routes/collectionCrm.route.ts)  — add CRM collection entry`
`GET  /collection-crm/all  ->  CollectionCrmController.getAllCollections  (src/routes/collectionCrm.route.ts)  — get all collection entries`

### Common
`POST /common/ivr-menu-one  ->  CommonController.ivrMenuOne  (src/routes/common.route.ts)  — IVR menu 1 (mobile lookup)`
`POST /common/ivr-menu-two  ->  CommonController.ivrMenuTwo  (src/routes/common.route.ts)  — IVR menu 2 (action by keypress)`
`POST /common/customer-details  ->  CommonController.customerDetails  (src/routes/common.route.ts)  — get customer details`
`POST /common/get-bank-details  ->  CommonController.getBankDetails  (src/routes/common.route.ts)  — lookup bank by IFSC`
`GET  /common/aadhar-down  ->  CommonController.aadharDown  (src/routes/common.route.ts)  — check Aadhaar service downtime`
`POST /common/lead-status  ->  CommonController.leadStatus  (src/routes/common.route.ts)  — get lead status by mobile`

### CRM
`POST /crm/lead-update  ->  CRMController.leadUpdate  (src/routes/crm.route.ts)  — update lead status`
`POST /crm/emi-calculator  ->  CRMController.emiCalculator  (src/routes/crm.route.ts)  — calculate EMI`
`POST /crm/credit-details  ->  CRMController.creditDetails  (src/routes/crm.route.ts)  — save credit details`
`POST /crm/get-amount-to-disburse  ->  CRMController.getAmountToDisbursed  (src/routes/crm.route.ts)  — get disbursable amount`
`POST /crm/generate-emi  ->  CRMController.generateEMI  (src/routes/crm.route.ts)  — generate EMI schedule`
`POST /crm/update-payment  ->  CRMController.updatePayment  (src/routes/crm.route.ts)  — update payment record`
`POST /crm/apply-penalty  ->  CRMController.applyPanelty  (src/routes/crm.route.ts)  — apply penalty to EMI`
`GET  /crm/get-emis  ->  CRMController.getEmis  (src/routes/crm.route.ts)  — get EMI list for customer`
`POST /crm/docs-requirements  ->  CRMController.getDocsRequirements  (src/routes/crm.route.ts)  — get KFS/sanction doc data`
`GET  /crm/emi-loan-details  ->  CRMController.getEmiLoanDetails  (src/routes/crm.route.ts)  — get EMI loan details`
`POST /crm/payday-to-emi  ->  CRMController.paydayToEmiConversion  (src/routes/crm.route.ts)  — convert payday to EMI loan`
`POST /crm/upload-bulk-mandate  ->  CRMController.uploadBulkMandateFile  (src/routes/crm.route.ts)  — upload bulk mandate CSV`
`GET  /crm/bulk-mandate-data  ->  CRMController.getBulkMandateData  (src/routes/crm.route.ts)  — get bulk mandate data`
`GET  /crm/bulk-mandate-file-url  ->  CRMController.getUrlforBulkMandateFile  (src/routes/crm.route.ts)  — get bulk mandate file URL`
`POST /crm/payment-verification  ->  CRMController.paymentVerification  (src/routes/crm.route.ts)  — verify Razorpay payment`
`POST /crm/payu-payment-verification  ->  CRMController.payUPaymentVerification  (src/routes/crm.route.ts)  — verify PayU payment`

### Customer
`POST /customers/login  ->  CustomersController.customerLogin  (src/routes/customer.route.ts)  — customer OTP login`
`POST /customers/verify-otp  ->  CustomersController.verifyOtp  (src/routes/customer.route.ts)  — verify OTP`
`POST /customers/create-otp  ->  CustomersController.createOtpService  (src/routes/customer.route.ts)  — create/send OTP`
`POST /customers/verify-otp-service  ->  CustomersController.verifyOtpService  (src/routes/customer.route.ts)  — verify OTP (service)`
`GET  /customers/dashboard  ->  CustomersController.customerCheckForDashboard  (src/routes/customer.route.ts)  — get dashboard state`
`POST /customers/incompleteDetailsUpdate  ->  CustomersController.onePageReloan  (src/routes/customer.route.ts)  — submit loan details (BRE trigger)`
`POST /customers/check-repeat-case/:leadID  ->  CustomersController.onePageReloanv2  (src/routes/customer.route.ts)  — repeat loan application`
`GET  /customers/get-customer-journey  ->  CustomersController.getCustomerJourney  (src/routes/customer.route.ts)  — get next step for customer`
`POST /customers/update-emi-transactions  ->  CustomersController.updateEmiTransactions  (src/routes/customer.route.ts)  — update EMI transaction status`
`POST /customers/update-payout  ->  CustomersController.updatePayout  (src/routes/customer.route.ts)  — update payout/disbursal status`
`POST /customers/update-lead-status  ->  CustomersController.updateLeadStatus  (src/routes/customer.route.ts)  — update lead status`
`POST /customers/update-job-status  ->  CustomersController.updateJobStatus  (src/routes/customer.route.ts)  — update job/lead status`
`GET  /customers/repayment-page  ->  CustomersController.repaymentPage  (src/routes/customer.route.ts)  — get repayment page data`
`POST /customers/payday-repayment  ->  CustomersController.razorpayPaydayRepayment  (src/routes/customer.route.ts)  — initiate payday repayment`
`POST /customers/emi-repayment  ->  CustomersController.createOrderRepayment  (src/routes/customer.route.ts)  — initiate EMI repayment`
`POST /customers/payu-repayment-callback  ->  CustomersController.payUCallbackResponse  (src/routes/customer.route.ts)  — PayU repayment callback`
`POST /customers/payu-repayment-verify  ->  CustomersController.validatePayUTransaction  (src/routes/customer.route.ts)  — verify PayU transaction`
`GET  /customers/check-pdf  ->  CustomersController.checkPdf  (src/routes/customer.route.ts)  — generate/check sanction PDF`
`GET  /customers/emi-soa  ->  CustomersController.emiSoa  (src/routes/customer.route.ts)  — get EMI statement of account`
`GET  /customers/one-page-view  ->  CustomersController.getOnePageView  (src/routes/customer.route.ts)  — get one-page loan view`
`POST /customers/dsa-lead-creation  ->  CustomersController.dsaLeadCreation  (src/routes/customer.route.ts)  — DSA partner lead creation`
`POST /customers/dsa-pan-verification  ->  CustomersController.dsaPanVerification  (src/routes/customer.route.ts)  — DSA PAN verification (API key auth)`
`GET  /customers/loans  ->  CustomersController.customerLoans  (src/routes/customer.route.ts)  — list customer loans`
`POST /customers/save-name-email  ->  CustomersController.saveNameEmail  (src/routes/customer.route.ts)  — save customer name/email`
`POST /customers/auto-login  ->  CustomersController.autoLogin  (src/routes/customer.route.ts)  — auto login by JWT`
`POST /customers/pancard-dpd  ->  CustomersController.checkPancardDpd  (src/routes/customer.route.ts)  — check PAN DPD status`
`POST /customers/missing-payments  ->  CustomersController.getMissingPayments  (src/routes/customer.route.ts)  — trigger missing payment settlement`
`POST /customers/send-disbursal-document  ->  CustomersController.sendDisbursalDocument  (src/routes/customer.route.ts)  — send disbursal docs to SQS`
`POST /customers/partial-incomplete-update  ->  CustomersController.partialIncompleteDetailsUpdate  (src/routes/customer.route.ts)  — partial loan details update`
`GET  /customers/payment-status  ->  CustomersController.updatePaymentStatus  (src/routes/customer.route.ts)  — update payment status`

### Customer Bank Account
`GET  /customer-bank-account/list  ->  CustomerBankAccountController.getCustomerBankAccounts  (src/routes/customerBankAccount.route.ts)  — list bank accounts`
`POST /customer-bank-account/save  ->  CustomerBankAccountController.saveBankAccount  (src/routes/customerBankAccount.route.ts)  — save bank account`
`POST /customer-bank-account/confirm  ->  CustomerBankAccountController.confirmBankAccount  (src/routes/customerBankAccount.route.ts)  — confirm bank account`
`GET  /customer-bank-account/referrer-list  ->  CustomerBankAccountController.getReferrerBankAccounts  (src/routes/customerBankAccount.route.ts)  — list referrer bank accounts`
`POST /customer-bank-account/save-referrer  ->  CustomerBankAccountController.saveReferrerBankAccount  (src/routes/customerBankAccount.route.ts)  — save referrer bank account`
`POST /customer-bank-account/confirm-referrer  ->  CustomerBankAccountController.confirmReferrerBankAccount  (src/routes/customerBankAccount.route.ts)  — confirm referrer bank account`

### Document Dispatch
`POST /document-dispatch/init  ->  DocumentDispatchController.init  (src/routes/documentDispatch.route.ts)  — initialize document dispatch`
`POST /document-dispatch/mark-sent  ->  DocumentDispatchController.markSent  (src/routes/documentDispatch.route.ts)  — mark document as sent`
`POST /document-dispatch/error  ->  DocumentDispatchController.markError  (src/routes/documentDispatch.route.ts)  — mark document dispatch error`

### Event Funnel
`GET  /event-funnel/report  ->  EventFunnelController.getFunnelReport  (src/routes/eventFunnel.route.ts)  — get event funnel report`
`GET  /event-funnel/kfs-not-disbursed  ->  EventFunnelController.getKFSDoneNotDisbursed  (src/routes/eventFunnel.route.ts)  — get KFS done but not disbursed`

### Lender
`POST /lender/add-credentials  ->  LenderController.AddCredentials  (src/routes/lender.route.ts)  — add lender credentials`
`PUT  /lender/update-credentials  ->  LenderController.updateCredentials  (src/routes/lender.route.ts)  — update lender credentials`
`GET  /lender/get-credentials  ->  LenderController.getCredentials  (src/routes/lender.route.ts)  — get lender credentials by lead`

### Lentra
`POST /lentra/stp  ->  LentraController.lentraStp  (src/routes/lentra.route.ts)  — trigger Lentra STP workflow`
`GET  /lentra/repayment-data  ->  LentraController.getRepaymentData  (src/routes/lentra.route.ts)  — get Lentra repayment data`
`POST /lentra/payment-fund-in  ->  LentraController.paymentFundIn  (src/routes/lentra.route.ts)  — Lentra fund-in payment`
`POST /lentra/stp-fallback  ->  LentraController.retryStpProcess  (src/routes/lentra.route.ts)  — retry Lentra STP`
`POST /lentra/send-disbursal-docs  ->  LentraController.sendDisbursalDocs  (src/routes/lentra.route.ts)  — send disbursal documents`

### Loan Restructure
`GET  /loan-restructure/charges  ->  LoanRestructureController.loanRestructureCharges  (src/routes/loanRestructure.route.ts)  — get restructure charges`
`POST /loan-restructure/reason  ->  LoanRestructureController.loanRestructureReason  (src/routes/loanRestructure.route.ts)  — submit restructure reason`
`POST /loan-restructure/kfs  ->  LoanRestructureController.loanRestructureKfsAcceptance  (src/routes/loanRestructure.route.ts)  — accept restructure KFS`
`GET  /loan-restructure/kfs-view  ->  LoanRestructureController.loanRestructureKfsView  (src/routes/loanRestructure.route.ts)  — view restructure KFS`

### Logs
`POST /logs/update-sms  ->  LogsController.updateSMSLogs  (src/routes/logs.routes.ts)  — update Kaleyra SMS logs`

### Onboarding
`POST /onboarding/pan-verification  ->  CustomerOnboardingController.panVerification  (src/routes/onboarding.routes.ts)  — verify PAN card`
`POST /onboarding/pan-confirmation  ->  CustomerOnboardingController.panConfirmation  (src/routes/onboarding.routes.ts)  — confirm PAN card`
`POST /onboarding/aadhar-otp-surepass  ->  CustomerOnboardingController.aadharOtpSurepass  (src/routes/onboarding.routes.ts)  — send Aadhaar OTP (SurePass)`
`POST /onboarding/verify-aadhar-otp-surepass  ->  CustomerOnboardingController.verifyAadharOtpSurepass  (src/routes/onboarding.routes.ts)  — verify Aadhaar OTP (SurePass)`
`POST /onboarding/initiate-digilocker  ->  CustomerOnboardingController.initiateDigilocker  (src/routes/onboarding.routes.ts)  — initiate DigiLocker Aadhaar`
`GET  /onboarding/digilocker-callback  ->  CustomerOnboardingController.digilockerCallback  (src/routes/onboarding.routes.ts)  — DigiLocker OAuth callback`
`POST /onboarding/verify-aadhar-digilocker  ->  CustomerOnboardingController.verifyAadharDigilocker  (src/routes/onboarding.routes.ts)  — verify Aadhaar via DigiLocker`
`POST /onboarding/name-email  ->  CustomerOnboardingController.nameAndEmail  (src/routes/onboarding.routes.ts)  — save name and email`
`POST /onboarding/email  ->  CustomerOnboardingController.email  (src/routes/onboarding.routes.ts)  — save email`
`POST /onboarding/finbox-create-url  ->  CustomerOnboardingController.finboxCreateUrl  (src/routes/onboarding.routes.ts)  — create Finbox bank connect URL`
`POST /onboarding/finbox-bank-connect  ->  CustomerOnboardingController.finboxBankConnect  (src/routes/onboarding.routes.ts)  — process Finbox bank connect`
`POST /onboarding/penny-drop  ->  CustomerOnboardingController.pennyDrop  (src/routes/onboarding.routes.ts)  — initiate penny drop`
`POST /onboarding/emandate  ->  CustomerOnboardingController.emandate  (src/routes/onboarding.routes.ts)  — initiate e-mandate`
`POST /onboarding/emandate-callback  ->  CustomerOnboardingController.emandateCallback  (src/routes/onboarding.routes.ts)  — e-mandate payment callback`
`GET  /onboarding/approval-view  ->  CustomerOnboardingController.approvalView  (src/routes/onboarding.routes.ts)  — get approval/offer view`
`POST /onboarding/reference-details  ->  CustomerOnboardingController.referenceDetails  (src/routes/onboarding.routes.ts)  — save reference contacts`
`PUT  /onboarding/reference-details  ->  CustomerOnboardingController.updateReferenceDetails  (src/routes/onboarding.routes.ts)  — update reference contacts`
`GET  /onboarding/states  ->  CustomerOnboardingController.getStates  (src/routes/onboarding.routes.ts)  — get state auto-suggestions`
`POST /onboarding/key-facts  ->  CustomerOnboardingController.keyFacts  (src/routes/onboarding.routes.ts)  — get KFS document`
`POST /onboarding/key-facts-acceptance  ->  CustomerOnboardingController.keyFactsAcceptance  (src/routes/onboarding.routes.ts)  — accept KFS`
`POST /onboarding/hyperverge-start  ->  CustomerOnboardingController.hypervergeStart  (src/routes/onboarding.routes.ts)  — start HyperVerge onboarding`
`POST /onboarding/hyperverge-result  ->  CustomerOnboardingController.hypervergeResult  (src/routes/onboarding.routes.ts)  — get HyperVerge result`
`POST /onboarding/selfie-verify  ->  CustomerOnboardingController.selfieVerify  (src/routes/onboarding.routes.ts)  — verify selfie`
`POST /onboarding/referrar-penny-drop  ->  CustomerOnboardingController.referrarPennyDrop  (src/routes/onboarding.routes.ts)  — referrer penny drop`
`POST /onboarding/send-kfs  ->  CustomerOnboardingController.sendKfs  (src/routes/onboarding.routes.ts)  — send KFS document`

### Page Instructions
`GET  /page-instructions  ->  PageInstructionController.getPageInstruction  (src/routes/pageInstruction.route.ts)  — get instructions by page name`
`POST /page-instructions  ->  PageInstructionController.addPageInstruction  (src/routes/pageInstruction.route.ts)  — add page instruction`

### Payment
`POST /payment/initiate  ->  PaymentController.makePayment  (src/routes/payment.route.ts)  — initiate payment (PayU/Razorpay)`
`POST /payment/validate-payu  ->  PaymentController.validatePayuPayment  (src/routes/payment.route.ts)  — validate PayU payment response`
`POST /payment/validate-rpay  ->  PaymentController.validateRazorpayPayment  (src/routes/payment.route.ts)  — validate Razorpay payment`

### Referral
`POST /referral/create  ->  ReferralController.createAndGenerateReferrer  (src/routes/referral.route.ts)  — create referral and generate code`
`GET  /referral/url  ->  ReferralController.getReferrarUrl  (src/routes/referral.route.ts)  — get referral URL`
`GET  /referral/invite-status  ->  ReferralController.getInviteStatus  (src/routes/referral.route.ts)  — list invite statuses`
`GET  /referral/invite-status/:id  ->  ReferralController.getInviteStatusById  (src/routes/referral.route.ts)  — get invite status by ID`
`GET  /referral/tracking  ->  ReferralController.tracking  (src/routes/referral.route.ts)  — get referral tracking data`

### Report Summary
`GET  /report-summary  ->  reportSummary  (src/routes/reportSummary.route.ts)  — get report summary`
`GET  /score-history  ->  scoreHistory  (src/routes/reportSummary.route.ts)  — get credit score history`

### SMS Delivery Log
`POST /sms-delivery/textnation  ->  SmsDelieryLogController.textNationSmsVerify  (src/routes/smsDelieryLog.route.ts)  — TextNation SMS delivery webhook`
`POST /sms-delivery/msg91  ->  SmsDelieryLogController.msg91SmsVerify  (src/routes/smsDelieryLog.route.ts)  — MSG91 SMS delivery webhook`
`POST /sms-delivery/acquirit  ->  SmsDelieryLogController.aquiritSmsVerify  (src/routes/smsDelieryLog.route.ts)  — Acquirit SMS delivery webhook`

### SOA
`POST /soa/generate  ->  SoaController.generatePdf  (src/routes/soa.route.ts)  — generate statement of account PDF`
`POST /soa/sanction-data  ->  SoaController.sectionData  (src/routes/soa.route.ts)  — get sanction letter data`
`POST /soa/sanction-pdf  ->  SoaController.generateSectionPdf  (src/routes/soa.route.ts)  — generate sanction letter PDF`

### Step
`GET  /step/next-step  ->  StepController.getUserNextStep  (src/routes/step.route.ts)  — get user's next onboarding step`
`GET  /step/referrar-next-step  ->  StepController.getReferrarNextStep  (src/routes/step.route.ts)  — get referrer's next step`

### Webhooks
`POST /webhooks/razorpay-repayment  ->  WebhookController.repaymentWebhook  (src/routes/webhooks.routes.ts)  — Razorpay repayment webhook`
`POST /webhooks/razorpay-verification  ->  WebhookController.repaymentVerificationWebhook  (src/routes/webhooks.routes.ts)  — Razorpay e-mandate verification webhook`
`POST /webhooks/lentra-repayment  ->  WebhookController.lentraRepaymentWebhook  (src/routes/webhooks.routes.ts)  — Lentra repayment webhook`
`POST /webhooks/decentro-payment  ->  WebhookController.decTransactionStatus  (src/routes/webhooks.routes.ts)  — Decentro payment status webhook`

### WhatsApp
`POST /whatsapp/identify  ->  WhatsAppController.identifyCustomer  (src/routes/whatsApp.route.ts)  — identify customer via WhatsApp`
`POST /whatsapp/verify-pan  ->  WhatsAppController.verifyPanCard  (src/routes/whatsApp.route.ts)  — verify PAN via WhatsApp`
`POST /whatsapp/confirm-pan  ->  WhatsAppController.confirmPanCard  (src/routes/whatsApp.route.ts)  — confirm PAN via WhatsApp`
`POST /whatsapp/handle-existing  ->  WhatsAppController.handleExistingCustomer  (src/routes/whatsApp.route.ts)  — handle existing customer WhatsApp flow`
`POST /whatsapp/bre-eligibility  ->  WhatsAppController.checkBreEligibility  (src/routes/whatsApp.route.ts)  — check BRE eligibility via WhatsApp`

### Withdrawal
`POST /withdrawal/request  ->  WithdrawalController.processWithdrawal  (src/routes/withdrawal.routes.ts)  — process withdrawal request`
`GET  /withdrawal/eligibility  ->  WithdrawalController.checkEligibility  (src/routes/withdrawal.routes.ts)  — check withdrawal eligibility`
`GET  /withdrawal/history  ->  WithdrawalController.getTransactionHistory  (src/routes/withdrawal.routes.ts)  — get withdrawal transaction history`
`GET  /withdrawal/balance  ->  WithdrawalController.getAvailableBalance  (src/routes/withdrawal.routes.ts)  — get available balance`
`GET  /withdrawal/limits  ->  WithdrawalController.getWithdrawalLimits  (src/routes/withdrawal.routes.ts)  — get withdrawal limits`
`GET  /withdrawal/transaction/:transactionId  ->  WithdrawalController.getTransactionDetails  (src/routes/withdrawal.routes.ts)  — get transaction details`
`GET  /withdrawal/receipt/:transactionId  ->  WithdrawalController.generateReceipt  (src/routes/withdrawal.routes.ts)  — generate PDF receipt`
`GET  /withdrawal/preview-receipt  ->  WithdrawalController.previewReceipt  (src/routes/withdrawal.routes.ts)  — preview receipt template (dev)`
`POST /withdrawal/webhook  ->  WithdrawalController.handleWebhook  (src/routes/withdrawal.routes.ts)  — payment gateway webhook`

### Scheduled Jobs (CronJobService)
`CRON autoDisbursalCoverage  ->  CronJobService.autoDisbursalCoverage  (src/services/cronJobs/cronJobs.service.ts)  — auto approve repeat customers`
`CRON fetchEMIPayments  ->  CronJobService.fetchEMIPayments  (src/services/cronJobs/cronJobs.service.ts)  — run EMI auto-payment (e-mandate)`
`CRON checkUtm  ->  CronJobService.checkUtm  (src/services/cronJobs/cronJobs.service.ts)  — update UTM sources on leads`
`CRON managePaymentCron  ->  CronJobService.managePaymentCron  (src/services/cronJobs/cronJobs.service.ts)  — settle pending payments`
`CRON razorpayWebhookSettlement  ->  RazorPayPaymentSettlementCronService  (src/services/cronJobs/razorpayPaymentSettlementCron.ts)  — settle unprocessed Razorpay payments`
`CRON setReferralRewardsProcessing  ->  ReferralRewardsCronService  (src/services/cronJobs/referralRewards.cron.service.ts)  — process referral rewards`
`CRON requeuePendingDocumentsCron  ->  requeuePendingDocumentsCron  (src/services/cronJobs/documentDispatch.cron.ts)  — requeue pending document dispatches`
`CRON customerExpiredON30Days  ->  CustomerExpiryCron.leadExpiredOn30Days  (src/services/cronJobs/customerExpiryCron.ts)  — expire 30-day-old incomplete leads`
`CRON pushLentraToSQS  ->  CronJobService.pushLentraToSQS  (src/services/cronJobs/cronJobs.service.ts)  — push disbursed leads to Lentra STP queue`
`CRON updateLeadStatusAfterCheckCollection  ->  CronJobService.updateLeadStatusAfterCheckCollection  (src/services/cronJobs/cronJobs.service.ts)  — update lead status after collection check (every 15 min)`
`CRON updateLeadStatusAfterCheckCollectionEmi  ->  CronJobService.updateLeadStatusAfterCheckCollectionEmi  (src/services/cronJobs/cronJobs.service.ts)  — update EMI lead status (every 30 min)`

### SQS Consumers
`SQS missingPaymentSettleQueueUrl  ->  consumerLoop  (src/consumers/missing.payment.settlement.consumer.ts)  — settle missing payments`
`SQS emandateMissingPaymentSettleQueueUrl  ->  consumerLoop  (src/consumers/emandate.missing.payment.consumer.ts)  — settle e-mandate missing payments`
`SQS razorpaySqsQueueUrl  ->  startSqsConsumer  (src/consumers/razorpay.sqs.consumer.ts)  — process Razorpay SQS messages`

---

## DATA_MODELS
### MySQL (Knex)

`Customer  (src/database/mysql/customer.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, kfs_otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status  — relationships: has many Lead, has many CustomerAccount`

`Lead  (src/database/mysql/leads.ts)  — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, ip, callAssign, creditAssign, createdDate, em_id, step, kfs, bureauVersion, productID, ipc, lenderID, isRestructure, plateform, lms_type, journey_type`

`Loan  (src/database/mysql/loan.ts)  — fields: loanID, leadID, loanNo, customerID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, accountNo, accountType, bankIfsc, bank, bankBranch, status, utr, payout_status, lentra_push_status  — relationships: belongs to Lead`

`Credit  (src/database/mysql/credit.ts)  — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, status, principal, amountToBeRepayed, firstDueDate, gst, disbursalDate`

`Emi  (src/database/mysql/emi.ts)  — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, status, amountRemains, brokenPeriodIntrest, accessAmount, paymentReceived, waive_off_amount, is_deleted`

`Approval  (src/database/mysql/approval.ts)  — fields: approvalID, customerID, leadID, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, status, creditedBy, rejectionReason, employmentType`

`CustomerAccount  (src/database/mysql/customerAccount.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, bank_holder_name, isAadharVerified, isSelfieVerified, lentraCustomerBankDetailsId`

`Address  (src/database/mysql/address.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy`

`Employer  (src/database/mysql/employer.ts)  — fields: employerID, customerID, employerName, empEmail, empDob, empSalary, empDesignation, empWorkIndustry, employment, totalExperience, currentCompany, address, city, state, pincode, status`

`RazorpayMandate  (src/database/mysql/razorpay_mandate.ts)  — fields: id, customerID, accountNo, accountType, bank, ifsc, leadID, inv_id, entity, receipt, invoice_number, customer_id, cust_name, cust_email, cust_contact, order_id, status, short_url, type, token_id, emMaxamount, need_another_mandate, name_missmatch_reject`

`PennyDrop  (src/database/mysql/penny_drop.ts)  — fields: id, customerID, p_id, leadID, name, ifsc, bank_name, account_number, account_status, registered_name, logs, penny_status, uid, penny_drop_name_match, penny_type`

`Transaction/Transection  (src/database/mysql/transections.ts)  — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, deleted, gateway, createdAt, updatedAt, createdBy, updatedBy, amount, collectionID, emiID, transactionDate, remarks, payment_transaction_status, waiver, discount_type`

`Collection  (src/database/mysql/collection.ts)  — fields: collectionID, customerID, leadID, loanNo, collectedAmount, penaltyAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, collectionStatus, orderID, lenderID`

`OnlinePayment  (src/database/mysql/onlinepayment.ts)  — fields: pID, name, email, phone, service, typeProduct, toValue, message, razorpayOrderId, razorpayPaymentId, paymentStatus, makerstamp, updatestamp, status, approved_id, paymentType, method, leadID, device`

`StepTracker  (src/database/mysql/step_tracker.ts)  — fields: id, step_id, is_completed, created_at, updated_at, is_skippable, customer_id, lead_id  — relationships: belongs to StepControl`

`StepControl  (src/database/mysql/step-control.ts)  — fields: id, product_id, provider_id, step_name, step_display_name, step_order, next_route, is_active, current_route, dashboard_message1-4, should_recheck, referrer_step_order, required_steps`

`LeadApiLog  (src/database/mysql/lead_api_log.ts)  — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo`

`Lender  (src/database/mysql/lender.ts)  — fields: lenderID, name, sanction_letter, kfs_letter, agreement_letter, gst_no, pan_no, credentials, lender_info, status`

`LentraCustomerMapping  (src/database/mysql/lentra_customer_mappings.ts)  — fields: id, customerID, leadID, lms_id, los_id, loan_no, entity_id, bank_details_id, isNachNeeded, nachMandateId, nachStatus, stpStatus, mandateCanceled, workflow_id, reference_id, stp_retries, nach_retries`

`Referrer  (src/database/mysql/referrer.ts)  — fields: id, referrer, mobile, created_at, updated_at`

`Reference  (src/database/mysql/reference.ts)  — fields: referenceID, customerID, relation, name, address, city, state, pincode, contactNo, createdBy, createdDate, reference_verify, is_verified`

`UserMetadata  (src/database/mysql/user_metadata.ts)  — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image, created_at, updated_at`

`ApiKey  (src/database/mysql/apiKey.ts)  — fields: id, api_key, client_id, client_name, is_active, rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day, allowed_ips, metadata, blocked_until, blocked_reason, last_used_at`

`RateLimit  (src/database/mysql/rateLimit.ts)  — fields: id, api_key, client_id, requests_count, window_start, window_type`

`BureauApiLog  (src/database/mysql/bureauApiLog.ts)  — fields: id, request_id, api_key, client_id, user_id, reference_id, endpoint, method, request_data, response_data, http_status_code, processing_status, processing_time_ms, error_code, error_message, client_ip`

`PayuPaymentsSettledByCron  (src/database/mysql/payuPaymentsSettledByCron.ts)  — fields: id, transaction_id, status, leadID, createdAt`

`ShortUrl  (src/database/mysql/shortUrl.ts)  — fields: id, code, long_url, lead_id, opened, opened_at, expires_at`

`SMSLog  (src/database/mysql/smsLog.ts)  — fields: id, message, leadId, customerId, status, type, created_at, updated_at`

`RestructureLoan  (src/database/mysql/restructure_loan.ts)  — fields: id, parentLeadId, childLeadId, reason, status, loan_type, createdAt, updatedAt`

`EmiProcessingFailureLog  (src/database/mysql/emiProcessingFailureLogs.ts)  — fields: id, order_id, failure_type, error_message, status, created_at`

### MongoDB (Mongoose)

`EventLogs  (src/database/mongo/model/EventLogs.ts)  — fields: mobile, customerId, leadId, utmSource, userType, requestedFrom, eventName, eventDate, status, ip, createdAt`

`KaleyraLogs  (src/database/mongo/model/KaleyraLogs.ts)  — fields: mobile, req_url, api_request, api_response, curl_error, type, created_at`

`LentraApiLogs  (src/database/mongo/model/LentraLogs.ts)  — fields: apiRequest, apiResponse, apiType, customerID, leadID, createdAt, updatedAt`

`RazorpayWebhookLogs  (src/database/mongo/model/RazorpayWeebhookLogs.ts)  — fields: id, subscriptionId, response, createdAt, updatedAt`

`EmiAutoPaymentCronLog  (src/database/mongo/model/EmiAutoPaymentCronLog.ts)  — fields: emiIDs, individualRecord (emiID, razorpay_mendate_id, status, errorMessage, step), createdAt, updatedAt`

`CustomerAssetData  (src/database/mongo/model/CustomerAssetData.ts)  — fields: userId, leadId, shakey, customerAsset`

`DocumentDispatch  (src/database/mongo/model/documentDispatch.model.ts)  — fields: leadId, customerId, documents (agreement, disbursal, kfs each with sent/sentAt/error), retryCount, lastError, createdAt, updatedAt`

`TrakierInstallInfo  (src/database/mongo/model/TrakierInstallInfo.ts)  — fields: partner, evid, eval, ets, crtd, cuid, cname, cphone, cmail, inside`

`User (Mongo)  (src/database/mongo/model/User.ts)  — fields: name, email, password`

### Prisma (MySQL)

`User  (src/database/prisma/schema.prisma)  — fields: id (Int, PK), email (String, unique), password (String)`
