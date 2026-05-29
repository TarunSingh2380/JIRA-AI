## ARCHITECTURE
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

## ROUTES
### Auth (`src/routes/auth.routes.ts`)
```
POST /new-api/auth/forget-password           → forgetPassword             (auth.controller.ts)      — Password reset
POST /new-api/auth/reset-password            → resetPassword              (auth.controller.ts)      — Reset password
GET  /new-api/auth/login-list                → loginList                  (auth.controller.ts)      — Login list
POST /new-api/auth/verify-google             → verifyGoogleAuth           (auth.controller.ts)      — Google OAuth verify
POST /new-api/auth/truecaller-init           → trueCallerInit             (auth.controller.ts)      — TrueCaller init
POST /new-api/auth/truecaller-callback       → trueCallerCallback         (auth.controller.ts)      — TrueCaller callback
POST /new-api/auth/truecaller-login          → trueCallerLogin            (auth.controller.ts)      — TrueCaller login
```

### Customer (`src/routes/customer.route.ts`)
```
POST /new-api/customers/login                        → customerLoginByMobile         (customers.controller.ts) — Send OTP
POST /new-api/customers/verify-otp                   → verifyOtp                     (customers.controller.ts) — Verify OTP & login
POST /new-api/customers/auth                         → authGenerationService         (customers.controller.ts) — Auth token generation
POST /new-api/customers/dsa-auth                     → dsaAuthGenerationService      (customers.controller.ts) — DSA auth
POST /new-api/customers/onboard-without-otp          → customerOnboardWithoutOtp     (customers.controller.ts) — Onboard without OTP
POST /new-api/customers/google-login                 → customerLoginByGoogle         (customers.controller.ts) — Google login
POST /new-api/customers/truecaller-login             → customerLoginByTrueCaller     (customers.controller.ts) — TrueCaller login
GET  /new-api/customers/dashboard                    → customerCheckForDashboard     (customers.controller.ts) — Dashboard data
POST /new-api/customers/check-pan-dedup              → (inline)                      (customers.controller.ts) — PAN dedup check
POST /new-api/customers/incompleteDetailsUpdate      → onePageReloan                 (customers.controller.ts) — Update onboarding details
POST /new-api/customers/partialIncompleteDetailsUpdate → partialIncompleteDetailsUpdate (customers.controller.ts) — Partial details update
POST /new-api/customers/check-repeat-case/:leadID    → onePageReloanv2               (customers.controller.ts) — Repeat case check
POST /new-api/customers/check-kyc-feature            → kycFeature                   (customers.controller.ts) — KYC feature flag
POST /new-api/customers/bureau-decision              → (bureauDecision)              (customers.controller.ts) — Bureau decision API
POST /new-api/customers/dsa-pan-verification         → (dsaPanVerification)          (customers.controller.ts) — DSA PAN verification
POST /new-api/customers/dsa-lead-creation            → (dsaLeadCreation)             (customers.controller.ts) — DSA lead creation
GET  /new-api/customers/dsa-lead-status              → dsaCheckLeadStatus            (customers.controller.ts) — DSA lead status
POST /new-api/customers/ongoing-status               → checkOngoingStatusService     (customers.controller.ts) — Check ongoing status
POST /new-api/customers/apptrove-artham-data         → processApptroveArthamData     (customers.controller.ts) — Apptrove/Artham data
POST /new-api/customers/pan-mobile-auto-fetch        → panMobileAutoFetchService     (customers.controller.ts) — Auto-fetch PAN/mobile
```

### Onboarding (`src/routes/onboarding.routes.ts`)
```
POST /new-api/customer_onboarding/pan-verification                → panFetch                        (onboarding.controller.ts) — PAN verify (Surepass)
POST /new-api/customer_onboarding/pan-verification-v2            → panFetchDigitap                  (onboarding.controller.ts) — PAN verify (Digitap)
POST /new-api/customer_onboarding/pan-confirmation               → panConfirmation                  (onboarding.controller.ts) — Confirm PAN
POST /new-api/customer_onboarding/send-aadhar-otp                → sendAadharOtp                    (onboarding.controller.ts) — Send Aadhaar OTP
POST /new-api/customer_onboarding/verify-aadhar-otp              → verifyAadharOtp                  (onboarding.controller.ts) — Verify Aadhaar OTP
POST /new-api/customer_onboarding/initiate-digilocker            → initiateDigilocker               (onboarding.controller.ts) — Initiate Digilocker
GET  /new-api/customer_onboarding/aadhar-verification-webhook    → aadharVerificationWebhook        (onboarding.controller.ts) — Digilocker callback
POST /new-api/customer_onboarding/aadhar-verification-webhook-v2 → aadharVerificationWebhookV2      (onboarding.controller.ts) — Digilocker v2 callback
POST /new-api/customer_onboarding/basic-details                  → saveBasicDetails                 (onboarding.controller.ts) — Save employment/income details
POST /new-api/customer_onboarding/finbox-bank-connect            → finboxBankConnect                (onboarding.controller.ts) — Finbox bank connect
POST /new-api/customer_onboarding/finbox-bank-connect-status     → finboxBankConnectStatus          (onboarding.controller.ts) — Finbox bank connect status
POST /new-api/customer_onboarding/initiate-penny-drop            → pennyDropInitiate                (onboarding.controller.ts) — Initiate penny drop
POST /new-api/customer_onboarding/verify-penny-drop              → pennyDropVerify                  (onboarding.controller.ts) — Verify penny drop
POST /new-api/customer_onboarding/set-emandate                   → setEmandate                      (onboarding.controller.ts) — Set e-mandate
POST /new-api/customer_onboarding/key-fact-statement             → keyFactStatement                 (onboarding.controller.ts) — KFS acceptance
POST /new-api/customer_onboarding/approval-view                  → approvalView                     (onboarding.controller.ts) — Loan approval view
POST /new-api/customer_onboarding/approval-view-v2              → approvalViewV2                    (onboarding.controller.ts) — Loan approval view v2
POST /new-api/customer_onboarding/reference-details             → saveReferenceDetails              (onboarding.controller.ts) — Save references
POST /new-api/customer_onboarding/update-reference-details      → updateReferenceDetails            (onboarding.controller.ts) — Update references
POST /new-api/customer_onboarding/selfie-verification           → verifySelfie                      (onboarding.controller.ts) — Selfie liveness
POST /new-api/customer_onboarding/verify-selfie-hyperverge      → verifyHypervergeSelfie            (onboarding.controller.ts) — Hyperverge selfie
POST /new-api/customer_onboarding/ckyc-search                   → ckycSearch                        (onboarding.controller.ts) — CKYC search
POST /new-api/customer_onboarding/verify-email-otp              → verifyEmailOtp                    (onboarding.controller.ts) — Verify email OTP
POST /new-api/customer_onboarding/get-basic-details             → getBasicDetails                   (onboarding.controller.ts) — Get basic details
POST /new-api/customer_onboarding/initiate-digilocker-v2        → initiateDigilockerV2              (onboarding.controller.ts) — Digilocker v2 initiate
```

### Customer Bank Account (`src/routes/customerBankAccount.route.ts`)
```
POST /new-api/customer_bank_account/save-bank-details       → saveBankAccount          (customerBankAccount.controller.ts) — Save bank account
POST /new-api/customer_bank_account/update-bank-details     → updateBankDetails        (customerBankAccount.controller.ts) — Update bank details
GET  /new-api/customer_bank_account/bank-accounts           → getCustomerBankAccounts  (customerBankAccount.controller.ts) — List bank accounts
GET  /new-api/customer_bank_account/bank-details-ifsc       → getBankDetailsOnIfsc     (customerBankAccount.controller.ts) — Lookup bank by IFSC
GET  /new-api/customer_bank_account/bank-account/:id        → getBankAccountById       (customerBankAccount.controller.ts) — Get account by ID
POST /new-api/customer_bank_account/confirm-bank-account    → confirmBankAccount       (customerBankAccount.controller.ts) — Confirm bank account
POST /new-api/customer_bank_account/mandate-feature         → getMandateFeature        (customerBankAccount.controller.ts) — Check mandate requirement
```

### Step (`src/routes/step.route.ts`)
```
POST /new-api/step/next-step   → getUserNextStep   (step.controller.ts) — Get next onboarding step for customer
```

### CRM (`src/routes/crm.route.ts`)
```
POST /new-api/crm/lead-update              → leadUpdate              (crm.controller.ts) — Update lead
POST /new-api/crm/emi-calculator           → emiCalculator           (crm.controller.ts) — Calculate EMI
POST /new-api/crm/credit-details           → creditDetails           (crm.controller.ts) — Create credit record
POST /new-api/crm/generate-emi             → generateEMI             (crm.controller.ts) — Generate EMI schedule
POST /new-api/crm/update-payment           → updatePayment           (crm.controller.ts) — Update payment
POST /new-api/crm/paydayToEmiConversion    → paydayToEmiConversion   (crm.controller.ts) — Convert payday to EMI
```

### Event Funnel (`src/routes/eventFunnel.route.ts`)
```
POST /new-api/event-funnel/save-frontend-events          → saveFrontendEventLogs    (eventFunnel.controller.ts) — Save frontend events
POST /new-api/event-funnel/save-third-party-events       → saveThirdPartyEventLogs  (eventFunnel.controller.ts) — Save third-party events
GET  /new-api/event-funnel/funnel-report                 → getFunnelReport          (eventFunnel.controller.ts) — Get funnel analytics
```

### Lentra (`src/routes/lentra.route.ts`)
```
POST /new-api/lentra/stp                  → lentraStp              (lentra.controller.ts) — Lentra STP flow
POST /new-api/lentra/unique-check         → uniqueCheck            (lentra.controller.ts) — Lentra unique check
GET  /new-api/lentra/repayment-data       → getRepaymentData       (lentra.controller.ts) — Lentra repayment data
GET  /new-api/lentra/repayment-page       → repaymentPage          (lentra.controller.ts) — Repayment page data
```

### Lender (`src/routes/lender.route.ts`)
```
POST /new-api/lender/get-credentials   → getCredentials   (lender.controller.ts) — Get lender credentials
```

### Webhooks (`src/routes/webhooks.route.ts`)
```
POST /new-api/webhooks/razorpay              → razorpayWebhook        (webhooks.controller.ts) — Razorpay payment webhook
POST /new-api/webhooks/razorpay-verification → razorpayVerification   (webhooks.controller.ts) — Razorpay verification webhook
POST /new-api/webhooks/decentro-payment      → decentroPaymentWebhook (webhooks.controller.ts) — Decentro payment webhook
```

### Health Check (inline in `app.ts`)
```
GET /health   → (inline)   (app.ts) — Health check endpoint
```

---

## DATA_MODELS
### MySQL (Knex/Objection)

**Customer & Identity:**
`ICustomer  (src/interfaces/customer.interface.ts)` — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, kfs_otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, client_key, client_id, plateform, consent, source, medium

`ICustomerAccount  (src/interfaces/customerAccount.interface.ts)` — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, bank_holder_name, is_credit, iu_date, isActive, isAadharVerified, auto_verified, lentraCustomerBankDetailsId

`IMobileToken  (src/interfaces/mobileToken.interface.ts)` — fields: id, customerID, mobile, appID, credatedDate, imei, access_token, last_login, android_id, firebase_token, jwt_access_token

`ILead  (src/interfaces/lead.interface.ts)` — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, ip, em_id, step, kfs, productID, ipc, lenderID, isRestructure, plateform, journeyID, lms_type

`IAddress  (src/interfaces/address.interface.ts)` — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy

**Loan & Credit:**
`ILoan  (src/interfaces/loan.interface.ts)` — fields: loanID, leadID, loanNo, customerID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, accountNo, accountType, bankIfsc, bank, bankBranch, status, rejReason, disbursedBy, createdDate, utr, payout_status

`ICredit  (src/interfaces/credit.interface.ts)` — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, paneltyEmis, status, principal, amountToBeRepayed, firstDueDate, brokenPeriodIntrest, gst, created_at, disbursalDate

`IEmi  (src/interfaces/emi.interface.ts)` — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paymentID, status, amountRemains, waive_off_amount

`IApproval  (src/interfaces/approval.interface.ts)` — fields: approvalID, customerID, leadID, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, plateFormFee, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, status, formNo, employed, remark, creditedBy, rejectionReason

**KYC & Bureau:**
`ILeadsApiLog  (src/interfaces/leadApiLogs.interface.ts)` — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo, code, state, entity_id, accountID, external_reference_id

`IBureauDataModel  (src/interfaces/bureauData.interface.ts)` — fields: id, customerID, leadID, reference_id, affordability_generic, predicted_income, predicted_affordability, Decision, LoanAmount, version, createdDate, emi_eligible, loan_type, emi_max_tenure, long_term_tenure

`ICkycRecords  (src/interfaces/ckycRecords.interface.ts)` — fields: id, decentroTxnId, ckycNo, ckycReferenceId, firstName, lastName, fullName, mobNum, pan, gender, dob, masked_aadhaar, customerID

`IPennyDropModel  (src/interfaces/penny_drop.interface.ts)` — fields: id, customerID, p_id, leadID, name, ifsc, bank_name, account_number, account_status, registered_name, logs, penny_status, uid, penny_drop_name_match, penny_type

**Payments & Mandates:**
`IRazorpayMandate  (src/interfaces/razorpayMandate.interface.ts)` — fields: id, customerID, accountNo, accountType, bank, ifsc, leadID, inv_id, entity, receipt, customer_id, cust_name, cust_email, cust_contact, order_id, status, short_url, type, credated_date, uid, token_id, emMaxamount, res_response, need_another_mandate, name_missmatch_reject, lenderID

`ICollection  (src/interfaces/collection.interface.ts)` — fields: collectionID, customerID, leadID, loanNo, collectedAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, collectionStatus, orderID, opening_balance, closing_balance, total_interest, principal_amount

`IOnlinePayment  (src/interfaces/onlinepayment.interface.ts)` — fields: pID, name, email, phone, service, typeProduct, toValue, message, razorpayOrderId, razorpayPaymentId, paymentStatus, makerstamp, status, paymentType, method, leadID, device

**Step Control & Journey:**
`IStepControlModel  (src/interfaces/step-control.interface.ts)` — fields: id, product_id, provider_id, instrument_id, step_name, step_display_name, pre_step_name, post_step_name, step_order, next_route, is_active, created_at, created_by, current_route, prev_route, should_recheck, referrer_step_order, required_steps, vendor

`IStepTrackerModel  (src/interfaces/step-tracker.interface.ts)` — fields: id, step_id, is_completed, created_at, updated_at, is_skippable, customer_id, lead_id, stepName, provider_id, vendor

**Lender & Config:**
`ILender  (src/interfaces/lender.interface.ts)` — fields: lenderID, name, sanction_letter, kfs_letter, agreement_letter, gst_no, pan_no, credentials, created_date, iu_date, lender_info, status

`ILentraCustomerMapping  (src/interfaces/lentra.interface.ts)` — fields: id, customerID, leadID, lms_id, los_id, loan_no, entity_id, bank_details_id, nachStatus, stpStatus, mandateCanceled, workflow_id, reference_id, stp_retries, nach_retries

`IApiKey  (src/interfaces/bureau.interface.ts)` — fields: id, api_key, client_id, client_name, is_active, rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day, allowed_ips, metadata, blocked_until, blocked_reason, last_used_at

**Notifications & Logs:**
`INotification  (src/interfaces/notification.interface.ts)` — fields: notificationID, customerID, leadID, notification, type, subject, createdDate, mtype, uid

`IThirdPartyLogsModel  (src/interfaces/thirdPartyLogs.interface.ts)` — fields: id, customerID, leadID, api_supplier, api_type, api_endpoint_url, api_method, api_request, api_response, status, created_at

`IRazorpayLog  (src/interfaces/razorpay_logs.interface.ts)` — fields: id, customerID, leadID, req_url, api_request, api_response, type, created_at

`IEventLogsModel  (src/interfaces/eventlogs.interface.ts)` — fields: id, mobile, customerId, leadId, utmSource, userType, requestedFrom, eventName, eventDate, status, ip, createdAt, method

`IFraudgatorLog  (src/interfaces/fraudgator_log.interface.ts)` — fields: id, ip, api_type, lead_api_log_id, created_at, updated_at, customerID

**Employer & References:**
`IEmployer  (src/interfaces/employer.interface.ts)` — fields: employerID, customerID, employerName, empEmail, empDob, empSalary, empDesignation, empWorkIndustry, employment, totalExperience, currentCompany, address, city, state, pincode, status, verifiedBy, createdDate

`IReferenceModel  (src/interfaces/reference.interface.ts)` — fields: referenceID, customerID, relation, name, address, city, state, pincode, contactNo, createdBy, createdDate

**Other:**
`IUserMetadata  (src/interfaces/user_metadata.interface.ts)` — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image

`IFeatureControl  (src/interfaces/feature_control.interface.ts)` — fields: id, feature_name, status, is_override, override_params, client_id, auth_token, base_url

`IRewardTransaction  (src/interfaces/rewardTransaction.interface.ts)` — fields: id, customer_id, transaction_id, transaction_type, amount, tds_amount, net_amount, bank_account_id, payment_gateway, gateway_reference_id, gateway_response, description, status, failure_reason, metadata, created_at, updated_at, processed_at

---

### MongoDB (Mongoose)

`IEventLogs  (src/database/mongo/EventLogs.ts)` — fields: _id, mobile, customerId, leadId, utmSource, userType, requestedFrom, eventName, eventDate, status, ip, createdAt — relationships: none

`ILentraApiLogs  (src/interfaces/lentra.interface.ts)  (src/database/mongo/LentraLogs.ts)` — fields: _id, apiRequest, apiResponse, apiType, customerID, leadID, createdAt, updatedAt — relationships: none

`OtpLogs  (src/database/mongo/OtpLogs.ts)` — fields: customerID, mobile, req_url, api_request, api_response, curl_error, created_at, type, iu_date, platform — relationships: none

`IPaymentLogs  (src/interfaces/paymentLog.interface.ts)  (src/database/mongo/paymentLogs.ts)` — fields: _id, orderId, amount, status, processedBy, details (IRazorpayWebhook payload), createdAt, updatedAt — relationships: none

`IRazorpayWebhookLogs  (src/database/mongo/RazorpayWeebhookLogs.ts)` — fields: id, subscriptionId, response, createdAt, updatedAt — relationships: none

`IThirdPartyApiLogs  (src/interfaces/thirdPartylog.interface.ts)  (src/database/mongo/ThirdPartyLogs.ts)` — fields: mobile, reqUrl, apiRequest, apiResponse, apiHeaders, apiType, apiProvider, statusCode, success, createdAt, updatedAt — relationships: none

---

### Redis (in-memory/cache)

`PennyFlow map  (src/redis/cacheService.ts)` — key: `penny_flow_map:{customerId}`, value: PennyFlow enum — TTL: midnight reset — purpose: sticky penny drop flow assignment per customer

`Step control cache  (src/database/mysql/step-control.ts)` — key: step_control cache pattern — value: IStepControlModel[] — purpose: cache step control configurations to reduce DB reads

`LMS Flow map  (src/utils/lmsFlowDecider.ts)` — key: `LMS_FLOW:{leadId}`, value: LmsFlow enum — TTL: daily midnight reset — purpose: deterministic LMS routing (Lentra vs System)

`Email OTP  (src/utils/emailVerification.ts)` — key: `otp:email:{email}`, value: OTP string + expiry — purpose: temporary email OTP storage

`Abridge token  (src/utils/experianAbridge.ts)` — key: `abridge_token`, value: access token — purpose: cache Experian Abridge API token

`PAN provider  (src/helpers/flowDecider.ts)` — key: `pan_provider`, value: PanProvider enum — purpose: route PAN verification to Digitap or Surepass
