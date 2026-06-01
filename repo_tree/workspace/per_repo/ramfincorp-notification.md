## ARCHITECTURE
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

## ROUTES
**Index module**
`GET /`  →  `IndexController` (src/routes/index.route.ts)  — health/index check

**Logs module** (`src/routes/logs.routes.ts`)
`POST /logs/update-sms-logs`  →  `LogsController.updateSMSLogs`  (src/controllers/logs.controller.ts)  — update Kaleyra SMS delivery logs

**Notification module** (`src/routes/notification.route.ts`)
`POST /notification/send-sms`  →  `NotificationController` SMS handler  (src/controllers/notification.controller.ts)  — send SMS via configured vendor (TextNation/Acquirit/MSG91)
`POST /notification/send-whatsapp`  →  `NotificationController` WhatsApp handler  (src/controllers/notification.controller.ts)  — send WhatsApp template message
`POST /notification/send-firebase`  →  `NotificationController` Firebase handler  (src/controllers/notification.controller.ts)  — send Firebase push notification
`POST /notification/send-email`  →  `NotificationController` email handler  (src/controllers/notification.controller.ts)  — send email via configured provider
`POST /notification/new-loan`  →  `NotificationController` new-loan handler  (src/controllers/notification.controller.ts)  — trigger new loan notification

**BullMQ consumer (queue worker)**
Queue `third-party-api-logs`  →  `ThirdPartyLogConsumer.processJob`  (src/bull/consumers/thirdPartyLogs.consumer.ts)  — persist third-party API log from Redis queue to MongoDB

---

## DATA_MODELS
### MongoDB (Mongoose)

`EmailLog`  (src/database/mongo/model/email_logs.ts)  — fields: email_to, email_from, api_request, api_response, subject, createdAt, updatedAt

`SMSLog`  (src/database/mongo/model/sms_logs.ts)  — fields: mobile, templateID, api_request, api_response, entityID, createdAt, updatedAt

`FirebaseLog`  (src/database/mongo/model/firebase_logs.ts)  — fields: customerID, title, api_request, api_response, firebaseToken, createdAt, updatedAt

`WhatsappLog`  (src/database/mongo/model/whatsapp_logs.ts)  — fields: mobile, templateName, api_request, api_response, createdAt, updatedAt

`KaleyraLogs`  (src/database/mongo/model/KaleyraLogs.ts)  — fields: mobile, req_url, api_request, api_response, curl_error, type, created_at

`OtpLogs`  (src/database/mongo/model/OtpLogs.ts)  — fields: customerID, mobile, req_url, api_request, api_response, curl_error, created_at, type, iu_date, platform

`ThirdPartyApiLogs`  (src/database/mongo/model/ThirdPartyApiLogs.ts)  — fields: mobile, reqUrl, apiRequest, apiResponse, apiHeaders, apiType, apiProvider, statusCode, success, createdAt, updatedAt, vendorId, env

`RazorpayWebhookLogs`  (src/database/mongo/model/RazorpayWeebhookLogs.ts)  — fields: subscriptionId, response, createdAt, updatedAt

`EmiAutoPaymentCronLog`  (src/database/mongo/model/EmiAutoPaymentCronLog.ts)  — fields: emiIDs, individualRecord (emiID, razorpay_mendate_id, status, errorMessage, step), createdAt, updatedAt

`CustomerAssetData`  (src/database/mongo/model/CustomerAssetData.ts)  — fields: userId, leadId, shakey, customerAsset

`User` (Mongo)  (src/database/mongo/model/User.ts)  — fields: name, email, password

### MySQL (Knex)

`ICustomer`  (src/database/mysql/customer.ts / src/interfaces/customer.interface.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, employeeType, status, ...

`ILead`  (src/database/mysql/leads.ts)  — fields: leadID, customerID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, status, productID, ...

`IApproval`  (src/database/mysql/approval.ts)  — fields: approvalID, customerID, leadID, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, status, ...

`ICredit`  (src/database/mysql/credit.ts)  — fields: creditID, customerID, leadID, productID, roi, tenure, interest, repaymentAmount, principal, status, ...

`IEmi`  (src/database/mysql/emi.ts)  — fields: emiID, creditID, customerID, leadID, principal, interest, amountPayable, dueDate, status, ...

`ILoan`  (src/database/mysql/loan.ts)  — fields: loanID, leadID, loanNo, customerID, disbursalAmount, disbursalDate, accountNo, bankIfsc, status, ...

`IMobileToken`  (src/database/mysql/mobileToken.ts)  — fields: id, customerID, mobile, appID, imei, access_token, firebase_token, jwt_access_token, last_login

`INotification`  (src/database/mysql/notification.ts)  — fields: notificationID, customerID, leadID, notification, type, subject, createdDate

`IAddress`  (src/database/mysql/address.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status

`IEmployer`  (src/database/mysql/employer.ts)  — fields: employerID, customerID, employerName, empEmail, empSalary, employment, city, state

`IRazorpayMandate`  (src/database/mysql/razorpay_mandate.ts)  — fields: id, customerID, accountNo, accountType, bank, ifsc, leadID, status, token_id, emMaxamount, ...

`IPennyDropModel`  (src/database/mysql/penny_drop.ts)  — fields: id, customerID, p_id, leadID, name, ifsc, bank_name, account_number, penny_status, ...

`ICustomerAccount`  (src/database/mysql/customerAccount.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, status

`IThirdPartyLogsModel`  (src/database/mysql/thirdPartyLogs.ts)  — fields: id, customerID, leadID, api_supplier, api_type, api_endpoint_url, api_method, api_request, api_response, status

`IUserMetadata`  (src/database/mysql/user_metadata.ts)  — fields: id, customerID, mobile, panVerify, aadharVerify, aadhar_mask, metaJSON, profile_image

`IStepTrackerModel`  (src/database/mysql/step_tracker.ts)  — fields: id, step_id, is_completed, customer_id, lead_id, is_skippable

`IStepControlModel`  (src/database/mysql/step-control.ts)  — fields: id, product_id, step_name, step_order, next_route, current_route, is_active, provider_id

`IMailTemplate`  (src/database/mysql/mail_template.ts)  — fields: id, name, subject, message

`IKaleyraLog` (MySQL)  (src/database/mysql/kaleyraLogs.ts)  — fields: mobile, req_url, api_request, api_response, curl_error, type, created_at

### MySQL (Prisma)

`User`  (src/database/prisma/schema.prisma)  — fields: id (Int PK autoincrement), email (String unique), password (String)
