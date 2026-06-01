## ARCHITECTURE

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

## ROUTES

Route handler implementations are skeletonized; exact line numbers are unavailable. Paths and handlers are derived from route files.

**IndexRoute (`src/routes/index.route.ts`)**
- `GET /`  →  `IndexController` handler  (src/routes/index.route.ts)  — health/index check

**AuthRoute (`src/routes/auth.route.ts`)**
- Routes unclear from source — `AuthController` is instantiated but handler methods are not visible in skeletonized source

**BreRoute (`src/routes/bre.route.ts`)**  
Authentication + validation middleware applied; exact paths unclear from source — `BreController` methods:
- Likely `POST /bre/check`  →  `BreController` + `validateBreRequestMiddleware`  — BRE CIBIL check and update
- Likely `POST /bre/finbox`  →  `BreController` + `validateFinboxRequestMiddleware`  — post-finbox BRE processing
- Likely `POST /bre/banking-surrogate`  →  `BreController` + `validateCheckMandateRequestMiddleware`  — banking surrogate / disable emandate check

**CibilRoute (`src/routes/cibil.route.ts`)**
- `POST` (path unclear)  →  `CibilController` + `validatePayload(getCibilScoreSchema)`  — fetch CIBIL credit score

**ExperianRoute (`src/routes/experian.route.ts`)**
- `POST` (path unclear)  →  `ExperianController` + `validatePayload(experianBureauDetailsSchema)`  — Experian hard-pull bureau details

**LoanListViewRoute (`src/routes/loanListView.route.ts`)**
- `POST` (path unclear)  →  `LoanListViewController` + `validateLoanListViewRequestMiddleware`  — fetch eligible loan product list for a customer

**BullMQ Queue Consumer**
- Queue: `"third-party-api-logs"`  →  `ThirdPartyLogProducer.produce()`  (src/bull/producer/thirdPartyLog.producer.ts)  — async third-party API log persistence

---

## DATA_MODELS

### MySQL (Knex)

`ICustomer`  (src/interfaces/customer.interface.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, kfs_otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, emandate_required, email_verification_status, step

`ILead`  (src/interfaces/lead.interface.ts)  — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, ip, em_id, kfs, bureauVersion, productID, ipc, lenderID, isRestructure, plateform

`IApproval`  (src/interfaces/approval.interface.ts)  — fields: approvalID, customerID, leadID, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, status, remark, creditedBy, rejectionReason, createdDate, employmentType

`ILoan`  (src/interfaces/loan.interface.ts)  — fields: loanID, leadID, loanNo, customerID, disbursalAmount, disbursalDate, accountNo, bankIfsc, bank, status, disbursedBy, createdDate, utr, payout_status

`ICredit`  (src/interfaces/credit.interface.ts)  — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, status, principal, amountToBeRepayed, firstDueDate, gst

`IEmi`  (src/interfaces/emi.interface.ts)  — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paymentID, status, amountRemains, waive_off_amount

`ICustomerAccount`  (src/interfaces/customerAccount.interface.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, bank_holder_name, is_credit

`IAddress`  (src/interfaces/address.interface.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate

`IDocument`  (src/interfaces/document.interface.ts)  — fields: documentID, customerID, documentType, documentFile, password, status, verifiedBy, verifiedDate, uploadBy, uploadedDate, type, upload_platform

`IEmployer`  (src/interfaces/employer.interface.ts)  — fields: employerID, customerID, employerName, empEmail, empDob, empSalary, empDesignation, empWorkIndustry, employment, totalExperience, currentCompany, address, city, state, pincode, status

`IMobileToken`  (src/interfaces/mobileToken.interface.ts)  — fields: id, customerID, mobile, appID, credatedDate, imei, access_token, last_login, android_id, firebase_token, jwt_access_token

`IUser`  (src/interfaces/users.interface.ts)  — fields: userID, name, email, mobile, branch, userName, password, role, status, createdBy, createdDate, accessPer, utype, lip, lead_status, otp, mac_address

`IBureauDataModel`  (src/interfaces/bureauData.interface.ts)  — fields: id, customerID, leadID, reference_id, Decision, LoanAmount, version, emi_eligible, emi_max_tenure, emi_max_monthly_amt, long_term_emi_eligible, personal_loan_decision, loan_type, disable_mandate, emi_roi

`ILeadsApiLog`  (src/interfaces/lead_api_log.interface.ts)  — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo

`ICreditReport`  (src/interfaces/credit_report.interface.ts)  — fields: id, cr_provider, bucket_id, customerID, stage_one_id, stage_two_id, errors, status, score, initiated_by, created_at

`ICreditScoreUserJourney`  (src/interfaces/credit_socore_user_journey.interface.ts)  — fields: id, step, attempt, customerID

`ICollection`  (src/interfaces/collection.interface.ts)  — fields: collectionID, customerID, leadID, loanNo, collectedAmount, collectedMode, collectedDate, referenceNo, discountAmount, status, collectedBy, collectionStatus, orderID, lenderID

`ITransection`  (src/interfaces/transections.interface.ts)  — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, gateway, createdAt, createdBy, amount, emiID, transactionDate, remarks, waiver

`IStepTrackerModel`  (src/interfaces/step-tracker.ts)  — fields: id, step_id, is_completed, customer_id, lead_id, is_skippable

`IStepControlModel`  (src/interfaces/step-control.interface.ts)  — fields: id, product_id, step_name, step_order, next_route, current_route, is_active, should_recheck

`IRepayDateHolidayModel`  (src/interfaces/repayDateHoliday.interface.ts)  — fields: id, repaydate

`ILender`  (src/interfaces/lender.interface.ts)  — fields: lenderID, name, sanction_letter, kfs_letter, agreement_letter, gst_no, pan_no, credentials, status, lender_info

`ILenderCreds`  (src/interfaces/lender_creds.interface.ts)  — fields: lenderID, cred_name, credentials, status

`IBankingDataModel`  (src/interfaces/bankingData.interface.ts)  — fields: id, customerID, leadID, reference_id, Decision, LoanAmount, version, personal_loan_decision

`IBankingBreOfferData`  (src/interfaces/bankingBreOfferData.interface.ts)  — fields: id, leadID, loan_type, approved_tenures, approved_amount, roi, bre_version, status, decision_payload

`IBreApprovalAmountModel`  (src/interfaces/breApprovalAmount.interface.ts)  — fields: id, customerID, leadID, type, amount

`IThirdPartyLogsModel`  (src/interfaces/thirdPartyLogs.interface.ts)  — fields: id, customerID, leadID, api_supplier, api_type, api_endpoint_url, api_method, api_request, api_response, status

`IUserMetadata`  (src/interfaces/user_metadata.interface.ts)  — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image

`IEMITransaction`  (src/interfaces/emi_transections.interface.ts)  — fields: transaction_id, order_id, emi_id, interest, principal, penalty, dpd_amount, transaction_date, lead_id, emi_status

`IOnlinePayment`  (src/interfaces/onlinepayment.interface.ts)  — fields: pID, name, email, phone, service, typeProduct, toValue, razorpayOrderId, razorpayPaymentId, paymentStatus, status, leadID

`IRazorpayMandate`  (src/interfaces/razorpay_mandate.interface.ts)  — fields: id, customerID, accountNo, bank, ifsc, leadID, order_id, status, token_id, emMaxamount, lenderID

`IAttributions`  (src/interfaces/attributions.interface.ts)  — fields: id, customerID, source, medium, campaign, createdDate

`ICallHistoryModel`  (src/interfaces/callHistory.interace.ts)  — fields: callHistoryID, customerID, leadID, callType, status, noteli, remark, callbackTime, calledBy

`IApiReqResLog`  (src/interfaces/api_req_res_log.interface.ts)  — fields: id, customerID, mobile, api_request, api_response, status, message, api_name

`IEmandateNotRequiredLogsModel`  (src/interfaces/emandate_not_required_logs.interface.ts)  — fields: id, customerID, nr_startBy, nr_startDate, nr_endBy, nr_endDate

`IBureauCustomerToken`  (src/interfaces/bureauToken.interface.ts)  — fields: id, customerID, customerToken

`IUserSummary`  (src/interfaces/user_summary.interface.ts)  — fields: id, api_type, customerID, provider_id, json_value, Status, created_by

`ICrProfileAccounts`  (src/interfaces/crProfileAccounts.interface.ts)  — fields: id, report_id, profile_id, customerID, product_id, bank_name, account_no, loan_amount, current_balance, account_type, on_time_payments

`ICrProfileRepaymentData`  (src/interfaces/crProfileRepaymentData.ts)  — fields: id, report_id, profile_id, customerID, profile_account_id, repayment_status, repayment_date, account_type

`IEmiProcessingFailureLog`  (src/interfaces/emiProcessingFailureLogs.interface.ts)  — fields: id, order_id, failure_type, error_message, status, created_at

`ILeadsLastUtmModel`  (src/interfaces/leads_last_utm.interface.ts)  — fields: id, leadID, utmSource, utm_assigned_date

`IDocumentFinboxInterfaceModel`  (src/interfaces/documentFinbox.interface.ts)  — fields: documentID, customerID, leadID, entityID, type, statement_id, documentType, documentFile, status

### MongoDB

`IThirdPartyApiLogs`  (src/database/mongo/ThirdPartyLogs.ts / src/interfaces/thirdPartyApiLog.interface.ts)  — fields: mobile, reqUrl, apiRequest, apiResponse, apiHeaders, apiType, apiProvider, statusCode, success, createdAt, updatedAt  — Mongoose model with schema driven by `ThirdPartyApiLogProvider` and `ThirdPartyApiLogType` enums

`IEmiAutoPaymentCronLog`  (src/interfaces/emiautopaycronlog.interface.ts)  — fields: emiIDs, individualRecord (emiID, razorpay_mendate_id, status, errorMessage, step), createdAt  — extends Mongoose `Document`

`IEventLogs`  (src/interfaces/eventlogs.interface.ts)  — fields: _id, mobile, customerId, leadId, utmSource, userType, requestedFrom, eventName, eventDate, status, ip  — Mongoose document

`IRazorpayWebhookLogs`  (src/interfaces/razorpaywebhooklogs.interface.ts)  — fields: id, subscriptionId, response, createdAt  — extends Mongoose `Document`

`ITrakierInstallInfo`  (src/interfaces/trakierInstallInfo.ts)  — fields: partner, evid, eval, ets, crtd, cuid, cname, cphone, cmail, inside  — extends Mongoose `Document`