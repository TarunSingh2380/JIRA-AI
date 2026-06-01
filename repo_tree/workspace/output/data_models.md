# Data Models Map

## DSA-Backend

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

## DSA-Backend.raw

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

## Kamakshimoney-onboarding

### In-Memory / Redux (persisted to localStorage via redux-persist)

`AppState  (src/redux/slices/appSlice.js)`
— fields: loading (status, message), stepperDisable, triggerInstallOnce
— relationships: none

`UserState  (src/redux/slices/userSlice.js)`
— fields: mobile, requestId, customer, lead, employment, accountId, selectedLoanOffer, hasLoanOffer, upgradeLoanAmount, month12Clicked
— relationships: none

### localStorage (via Storage utility)

`Storage  (src/utils/storage.js)`
— keys: defined in KEYS export (exact key names unclear from source)
— operations: get, set, remove, clearAll

### API Request/Response Contracts (src/services/userService.js)

`customerLoginAPI`  — input: mobile; output: unclear from source

`verifyOTPAPI`  — input: requestId, otp

`panVerificationAPI`  — input: PAN fields (exact shape unclear from source)

`panConfirmationAPI`  — input: panNumber

`basicDetailsAPI`  — input: data object (fields unclear from source)

`generateAadhaarOTPAPI`  — input: aadharNo, accountId

`verifyAadhaarOTPAPI`  — input: aadharNo, otp, accountId

`selfieLivenessAPI`  — input: blob, accountId

`addBankDetailsAPI`  — input: values (account number, confirm account, IFSC), previousAccountID

`selectTenureAPI`  — input: none (uses session context)

`loanApprovalViewAPI`  — input: data (leadID, productID, amount, tenureDays, roi)

`emandateV2API`  — input: accountId

`pennyDropAPI`  — input: accountId; output: { data: { pennyStatus } }

`kfsPaydayAPI`  — input: none

`keyfactsAcceptanceAPI`  — input: none

`stepCheckerAPI`  — input: accountId, isReload

`paydayToEMIConversionAPI`  — input: values

`confirmBankAccountAPI`  — input: mandateId, accountID

`googleAuthAPI`  — input: token

`autoLoginAPI`  — input: token

`eventsFunnelAPI`  — input: eventName, attributes

`hyperVergeOnboardingAPI` / `hyperVergeResultAPI`  — inputs: none

`fetchAddress`  — input: pinCode

## Kamakshimoney-onboarding.raw

### In-Memory / Redux (persisted to localStorage via redux-persist)

`AppState  (src/redux/slices/appSlice.js)`
— fields: loading (status, message), stepperDisable, triggerInstallOnce
— relationships: none

`UserState  (src/redux/slices/userSlice.js)`
— fields: mobile, requestId, customer, lead, employment, accountId, selectedLoanOffer, hasLoanOffer, upgradeLoanAmount, month12Clicked
— relationships: none

### localStorage (via Storage utility)

`Storage  (src/utils/storage.js)`
— keys: defined in KEYS export (exact key names unclear from source)
— operations: get, set, remove, clearAll

### API Request/Response Contracts (src/services/userService.js)

`customerLoginAPI`  — input: mobile; output: unclear from source

`verifyOTPAPI`  — input: requestId, otp

`panVerificationAPI`  — input: PAN fields (exact shape unclear from source)

`panConfirmationAPI`  — input: panNumber

`basicDetailsAPI`  — input: data object (fields unclear from source)

`generateAadhaarOTPAPI`  — input: aadharNo, accountId

`verifyAadhaarOTPAPI`  — input: aadharNo, otp, accountId

`selfieLivenessAPI`  — input: blob, accountId

`addBankDetailsAPI`  — input: values (account number, confirm account, IFSC), previousAccountID

`selectTenureAPI`  — input: none (uses session context)

`loanApprovalViewAPI`  — input: data (leadID, productID, amount, tenureDays, roi)

`emandateV2API`  — input: accountId

`pennyDropAPI`  — input: accountId; output: { data: { pennyStatus } }

`kfsPaydayAPI`  — input: none

`keyfactsAcceptanceAPI`  — input: none

`stepCheckerAPI`  — input: accountId, isReload

`paydayToEMIConversionAPI`  — input: values

`confirmBankAccountAPI`  — input: mandateId, accountID

`googleAuthAPI`  — input: token

`autoLoginAPI`  — input: token

`eventsFunnelAPI`  — input: eventName, attributes

`hyperVergeOnboardingAPI` / `hyperVergeResultAPI`  — inputs: none

`fetchAddress`  — input: pinCode

## crm-kamakshimoney-frontend

This is a pure React frontend with no ORM or direct database access. All data is fetched from a backend REST API. The following describes the key data shapes used in Redux state and API contracts inferred from the source.

### In-Memory (Redux Store)

`userSlice  (src/redux/slices/userSlice.js)  — fields: userLogin, leadStatus, permissions, roleName, leadType, productID, repayDate, salaryDate, customerProfileInfo, userBlacklist`

`appSlice  (src/redux/slices/appSlice.js)  — fields: refreshData, collectionMode`

`navbarSlice  (src/redux/slices/navbarSlice.js)  — fields: navBarMenuIsLoad, navBarMenu`

`paginationSlice  (src/redux/slices/paginationSlice.js)  — fields: loading, currentPage, totalPage, totalItems`

### Persisted (localStorage via redux-persist)

`user  (src/redux/store.js)  — persisted slice: userSlice fields above`

### API Request/Response Shapes (inferred from service methods)

**Auth**
`LoginRequest  (src/services/AuthAPI.js)  — fields: username/email, password`
`VerifyOTPRequest  (src/services/AuthAPI.js)  — fields: otp, userID`
`ForgotPasswordRequest  (src/services/AuthAPI.js)  — fields: email`
`ChangePasswordRequest  (src/services/AuthAPI.js)  — fields: password, userID`

**Customer / Lead**
`CustomerProfile  (src/services/CustomerProfileAPI.js)  — fields: leadID, name, mobile, email, dob, gender, pancard, aadhar`
`LoanDetails  (src/services/CustomerProfileAPI.js)  — fields: productID, adminFee, loanAmount, tenure, repaymentDate`
`CreditDetails  (src/services/CustomerProfileAPI.js)  — fields: dpd (days past due), creditScore, loanStatus`
`CollectionDetails  (src/services/CustomerProfileAPI.js)  — fields: collectionID, paymentMode, amount, remainingCollection`
`EMISchedule  (src/services/CustomerProfileAPI.js)  — fields: emiDate, emiAmount, status`
`EmandateDetails  (src/services/CustomerProfileAPI.js)  — fields: emandateEnabled, accountID, emandateID`
`EmploymentDetails  (src/services/CustomerProfileAPI.js)  — fields: officialEmailId, designation, employer, salary`
`AddressDetails  (src/services/CustomerProfileAPI.js)  — fields: pincode, address, type`
`ReferencesDetails  (src/services/CustomerProfileAPI.js)  — fields: name, relation, mobile`
`PennyDrop  (src/services/CustomerProfileAPI.js)  — fields: bankAccount, ifsc, nameMatch`
`StatementOfAccount  (src/services/CustomerProfileAPI.js)  — fields: leadId, type (EMI/Payday)`

**Collection**
`WaiveOff  (src/services/CollectionAPI.js)  — fields: leadId, collectionID, waiveOffAmount`
`DndCustomer  (src/services/CollectionAPI.js)  — fields: customerID, removedBy`
`BulkEmandate  (src/services/CollectionAPI.js)  — fields: file (CSV/XLSX)`
`CollectionManageAction  (src/services/CollectionAPI.js)  — fields: action, collectionID, transactionID`

**Refund**
`RefundTransaction  (src/services/RefundAPI.js)  — fields: leadID, paymentID, orderID, mobileNo, loanNo, status, startDate, endDate`
`RefundDashboard  (src/services/RefundAPI.js)  — fields: startDate, endDate, status counts`
`BulkRefundUpload  (src/services/RefundAPI.js)  — fields: file (CSV), uploadStatus, failedS3Link`

**CRM Management**
`User  (src/services/CRMManagementAPI.js)  — fields: userID, name, role, permissions, password`
`Permission  (src/services/CRMManagementAPI.js)  — fields: permission_id, permission_name, type`
`Role  (src/services/CRMManagementAPI.js)  — fields: role_id, roleName, permissions[]`
`IPWhitelist  (src/services/CRMManagementAPI.js)  — fields: id, ipAddress`
`SourcingPartner  (src/services/CRMManagementAPI.js)  — fields: partnerName, formData`
`DSAPartner  (src/services/CRMManagementAPI.js)  — fields: dsaCredentials (unclear from source)`

**Disbursal**
`DisbursalRecord  (src/services/Disbursal.js)  — fields: leadIds[], disbursalAllocateArray`

**Quick Reports**
`QuickReportRequest  (src/services/QuickReportAPI.js)  — fields: payload, downloadColumns[], search (query string)`
`QuickReportDownload  (src/services/QuickReportAPI.js)  — fields: id, files (S3 URL)`

## crm-kamakshimoney-frontend.raw

This is a pure React frontend with no ORM or direct database access. All data is fetched from a backend REST API. The following describes the key data shapes used in Redux state and API contracts inferred from the source.

### In-Memory (Redux Store)

`userSlice  (src/redux/slices/userSlice.js)  — fields: userLogin, leadStatus, permissions, roleName, leadType, productID, repayDate, salaryDate, customerProfileInfo, userBlacklist`

`appSlice  (src/redux/slices/appSlice.js)  — fields: refreshData, collectionMode`

`navbarSlice  (src/redux/slices/navbarSlice.js)  — fields: navBarMenuIsLoad, navBarMenu`

`paginationSlice  (src/redux/slices/paginationSlice.js)  — fields: loading, currentPage, totalPage, totalItems`

### Persisted (localStorage via redux-persist)

`user  (src/redux/store.js)  — persisted slice: userSlice fields above`

### API Request/Response Shapes (inferred from service methods)

**Auth**
`LoginRequest  (src/services/AuthAPI.js)  — fields: username/email, password`
`VerifyOTPRequest  (src/services/AuthAPI.js)  — fields: otp, userID`
`ForgotPasswordRequest  (src/services/AuthAPI.js)  — fields: email`
`ChangePasswordRequest  (src/services/AuthAPI.js)  — fields: password, userID`

**Customer / Lead**
`CustomerProfile  (src/services/CustomerProfileAPI.js)  — fields: leadID, name, mobile, email, dob, gender, pancard, aadhar`
`LoanDetails  (src/services/CustomerProfileAPI.js)  — fields: productID, adminFee, loanAmount, tenure, repaymentDate`
`CreditDetails  (src/services/CustomerProfileAPI.js)  — fields: dpd (days past due), creditScore, loanStatus`
`CollectionDetails  (src/services/CustomerProfileAPI.js)  — fields: collectionID, paymentMode, amount, remainingCollection`
`EMISchedule  (src/services/CustomerProfileAPI.js)  — fields: emiDate, emiAmount, status`
`EmandateDetails  (src/services/CustomerProfileAPI.js)  — fields: emandateEnabled, accountID, emandateID`
`EmploymentDetails  (src/services/CustomerProfileAPI.js)  — fields: officialEmailId, designation, employer, salary`
`AddressDetails  (src/services/CustomerProfileAPI.js)  — fields: pincode, address, type`
`ReferencesDetails  (src/services/CustomerProfileAPI.js)  — fields: name, relation, mobile`
`PennyDrop  (src/services/CustomerProfileAPI.js)  — fields: bankAccount, ifsc, nameMatch`
`StatementOfAccount  (src/services/CustomerProfileAPI.js)  — fields: leadId, type (EMI/Payday)`

**Collection**
`WaiveOff  (src/services/CollectionAPI.js)  — fields: leadId, collectionID, waiveOffAmount`
`DndCustomer  (src/services/CollectionAPI.js)  — fields: customerID, removedBy`
`BulkEmandate  (src/services/CollectionAPI.js)  — fields: file (CSV/XLSX)`
`CollectionManageAction  (src/services/CollectionAPI.js)  — fields: action, collectionID, transactionID`

**Refund**
`RefundTransaction  (src/services/RefundAPI.js)  — fields: leadID, paymentID, orderID, mobileNo, loanNo, status, startDate, endDate`
`RefundDashboard  (src/services/RefundAPI.js)  — fields: startDate, endDate, status counts`
`BulkRefundUpload  (src/services/RefundAPI.js)  — fields: file (CSV), uploadStatus, failedS3Link`

**CRM Management**
`User  (src/services/CRMManagementAPI.js)  — fields: userID, name, role, permissions, password`
`Permission  (src/services/CRMManagementAPI.js)  — fields: permission_id, permission_name, type`
`Role  (src/services/CRMManagementAPI.js)  — fields: role_id, roleName, permissions[]`
`IPWhitelist  (src/services/CRMManagementAPI.js)  — fields: id, ipAddress`
`SourcingPartner  (src/services/CRMManagementAPI.js)  — fields: partnerName, formData`
`DSAPartner  (src/services/CRMManagementAPI.js)  — fields: dsaCredentials (unclear from source)`

**Disbursal**
`DisbursalRecord  (src/services/Disbursal.js)  — fields: leadIds[], disbursalAllocateArray`

**Quick Reports**
`QuickReportRequest  (src/services/QuickReportAPI.js)  — fields: payload, downloadColumns[], search (query string)`
`QuickReportDownload  (src/services/QuickReportAPI.js)  — fields: id, files (S3 URL)`

## crm-react

This is a pure frontend application. There are no ORM models or database schemas. Data is managed in Redux slices (in-memory) and persisted partially to `localStorage` via redux-persist.

### In-memory (Redux store — `src/redux/store.js`)

`userSlice`  (src/redux/slices/userSlice.js)  — fields: isLogin, permissions, roleName, leadStatus, leadType, productID, repayDate, salaryDate, customerProfileInfo, isBlacklisted  — relationships: persisted to localStorage via redux-persist

`appSlice`  (src/redux/slices/appSlice.js)  — fields: refreshData, collectionMode  — relationships: none

`paginationSlice`  (src/redux/slices/paginationSlice.js)  — fields: loading, currentPage, totalPage, totalItems  — relationships: consumed by all paginated list pages

`navbarSlice`  (src/redux/slices/navbarSlice.js)  — fields: isLoad, menu  — relationships: consumed by Navbar component

`apiSlice` / `apiSlices`  (src/redux/slices/apiSlice.js, apiSlices.js)  — dynamically generated per-endpoint slices  — fields: data, loading, error (generated)  — relationships: none

### localStorage (via redux-persist)

Only the `user` reducer is whitelisted for persistence. Token also stored independently via `storeToken`/`getToken` in `src/utils/storage.js` (localStorage key unclear from source).

### API contract shapes (inferred from service method parameters — not Pydantic/ORM, frontend-only)

`LoginPayload`  (src/services/AuthAPI.js)  — fields: username/email, password

`VerifyOTPPayload`  (src/services/AuthAPI.js)  — fields: otp, userID

`ChangeStatusPayload`  (src/services/CustomerProfileAPI.js)  — fields: status, leadID (plus status-specific fields)

`AddCollectionPayload`  (src/services/CustomerProfileAPI.js)  — fields: amount, date, paymentMode, transactionID (validated via `addCollectionEMIValidation`)

`WaiveOffPayload`  (src/services/CollectionAPI.js)  — fields: unclear from source

`RefundBulkPayload`  (src/services/RefundAPI.js)  — fields: CSV file upload (FormData)

`DisbursalInitiatePayload`  (src/services/Disbursal.js)  — fields: disbursalAllocateArray (array of leadIds)

`LeadAllocationPayload`  (src/services/LeadsAPI.js)  — fields: leadIds, userId (inferred from allocateMultipleLeadsAPI)

## crm-react.raw

This is a pure frontend application. There are no ORM models or database schemas. Data is managed in Redux slices (in-memory) and persisted partially to `localStorage` via redux-persist.

### In-memory (Redux store — `src/redux/store.js`)

`userSlice`  (src/redux/slices/userSlice.js)  — fields: isLogin, permissions, roleName, leadStatus, leadType, productID, repayDate, salaryDate, customerProfileInfo, isBlacklisted  — relationships: persisted to localStorage via redux-persist

`appSlice`  (src/redux/slices/appSlice.js)  — fields: refreshData, collectionMode  — relationships: none

`paginationSlice`  (src/redux/slices/paginationSlice.js)  — fields: loading, currentPage, totalPage, totalItems  — relationships: consumed by all paginated list pages

`navbarSlice`  (src/redux/slices/navbarSlice.js)  — fields: isLoad, menu  — relationships: consumed by Navbar component

`apiSlice` / `apiSlices`  (src/redux/slices/apiSlice.js, apiSlices.js)  — dynamically generated per-endpoint slices  — fields: data, loading, error (generated)  — relationships: none

### localStorage (via redux-persist)

Only the `user` reducer is whitelisted for persistence. Token also stored independently via `storeToken`/`getToken` in `src/utils/storage.js` (localStorage key unclear from source).

### API contract shapes (inferred from service method parameters — not Pydantic/ORM, frontend-only)

`LoginPayload`  (src/services/AuthAPI.js)  — fields: username/email, password

`VerifyOTPPayload`  (src/services/AuthAPI.js)  — fields: otp, userID

`ChangeStatusPayload`  (src/services/CustomerProfileAPI.js)  — fields: status, leadID (plus status-specific fields)

`AddCollectionPayload`  (src/services/CustomerProfileAPI.js)  — fields: amount, date, paymentMode, transactionID (validated via `addCollectionEMIValidation`)

`WaiveOffPayload`  (src/services/CollectionAPI.js)  — fields: unclear from source

`RefundBulkPayload`  (src/services/RefundAPI.js)  — fields: CSV file upload (FormData)

`DisbursalInitiatePayload`  (src/services/Disbursal.js)  — fields: disbursalAllocateArray (array of leadIds)

`LeadAllocationPayload`  (src/services/LeadsAPI.js)  — fields: leadIds, userId (inferred from allocateMultipleLeadsAPI)

## devOpsStack

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

## devOpsStack.raw

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

## kanakloans-webview

### In-Memory / Redux State (redux-persist → localStorage)

`appSlice`  (src/redux/slices/appSlice.js)  — fields: loading, stepperDisable, triggerInstallOnce — relationships: persisted under key "app"

`userSlice`  (src/redux/slices/userSlice.js)  — fields: mobile, requestId, customer, lead, employment, accountId, selectedLoanOffer, hasLoanOffer, upgradeLoanAmount, month12Clicked — relationships: persisted under key "user"

### localStorage (via `src/utils/storage.js` KEYS constants)

`Storage KEYS`  (src/utils/storage.js)  — fields: JWT_TOKEN, ACCESS_TOKEN, LEAD_ID (additional keys unclear from source — KEYS object body not fully exposed) — relationships: read by userService.js for API auth headers

### API Contract Shapes (inferred from service call parameters — not formal Pydantic/ORM models)

`customerLoginAPI payload`  (src/services/userService.js)  — fields: mobile

`verifyOTPAPI payload`  (src/services/userService.js)  — fields: requestId, otp

`panVerificationAPI payload`  (src/services/userService.js)  — fields: (parameters not fully exposed in source)

`addBankDetailsAPI payload`  (src/services/userService.js)  — fields: values (account number, re-account number, IFSC), previousAccountID

`loanApprovalViewAPI payload`  (src/services/userService.js)  — fields: data (structure unclear from source)

`paydayToEMIConversionAPI payload`  (src/services/userService.js)  — fields: values (structure unclear from source)

`confirmBankAccountAPI payload`  (src/services/userService.js)  — fields: mandateId, accountID

`verifyAadhaarOTPAPI payload`  (src/services/userService.js)  — fields: aadharNo, otp, accountId

`selfieLivenessAPI payload`  (src/services/userService.js)  — fields: blob (image), accountId

`eventsFunnelAPI payload`  (src/services/userService.js)  — fields: eventName, attributes (optional object)

## kanakloans-webview.raw

### In-Memory / Redux State (redux-persist → localStorage)

`appSlice`  (src/redux/slices/appSlice.js)  — fields: loading, stepperDisable, triggerInstallOnce — relationships: persisted under key "app"

`userSlice`  (src/redux/slices/userSlice.js)  — fields: mobile, requestId, customer, lead, employment, accountId, selectedLoanOffer, hasLoanOffer, upgradeLoanAmount, month12Clicked — relationships: persisted under key "user"

### localStorage (via `src/utils/storage.js` KEYS constants)

`Storage KEYS`  (src/utils/storage.js)  — fields: JWT_TOKEN, ACCESS_TOKEN, LEAD_ID (additional keys unclear from source — KEYS object body not fully exposed) — relationships: read by userService.js for API auth headers

### API Contract Shapes (inferred from service call parameters — not formal Pydantic/ORM models)

`customerLoginAPI payload`  (src/services/userService.js)  — fields: mobile

`verifyOTPAPI payload`  (src/services/userService.js)  — fields: requestId, otp

`panVerificationAPI payload`  (src/services/userService.js)  — fields: (parameters not fully exposed in source)

`addBankDetailsAPI payload`  (src/services/userService.js)  — fields: values (account number, re-account number, IFSC), previousAccountID

`loanApprovalViewAPI payload`  (src/services/userService.js)  — fields: data (structure unclear from source)

`paydayToEMIConversionAPI payload`  (src/services/userService.js)  — fields: values (structure unclear from source)

`confirmBankAccountAPI payload`  (src/services/userService.js)  — fields: mandateId, accountID

`verifyAadhaarOTPAPI payload`  (src/services/userService.js)  — fields: aadharNo, otp, accountId

`selfieLivenessAPI payload`  (src/services/userService.js)  — fields: blob (image), accountId

`eventsFunnelAPI payload`  (src/services/userService.js)  — fields: eventName, attributes (optional object)

## node-crm

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

## node-crm.raw

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

## node_crm

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

## node_crm.raw

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

## onboarding-service-frontend

No ORM or database models exist in this frontend repository. All persistent state is managed via Redux + `redux-persist` (localStorage).

**In-memory / Redux state (localStorage via redux-persist)**

`appSlice`  (src/redux/slices/appSlice.js) — fields: `loading.status`, `loading.message`, `stepperDisable`, `triggerInstallOnce`

`userSlice`  (src/redux/slices/userSlice.js) — fields: `mobile`, `requestId`, `customer`, `lead`, `employment`, `accountId`, `selectedLoanOffer`, `hasLoanOffer`, `upgradeLoanAmount`, `month12Clicked`, `isNewDigilocker`

**LocalStorage keys** (src/utils/storage.js) — `KEYS` object; specific key names unclear from source (skeletonized), but includes: `JWT_TOKEN`, `ACCESS_TOKEN`, `LEAD_ID` (referenced in service file comments)

**i18n locale schemas** (src/i18n/locales/en.json, hi.json, ka.json) — Not DB models; UI string maps for English, Hindi, Kannada. Keys cover: `login`, `panVerify`, `employmentDetails`, `selectLoanOffer`, `loanApproval`, `yourEmail`, `aadhaarVerification`, `cameraPermission`, `selfie`, `addBankAccount`, `pennyDrop`, `kfs`, `disbursed`, `loanRejected`, `finboxError`, `loaderMsg`, plus validation namespaces.

## onboarding-service-frontend.raw

No ORM or database models exist in this frontend repository. All persistent state is managed via Redux + `redux-persist` (localStorage).

**In-memory / Redux state (localStorage via redux-persist)**

`appSlice`  (src/redux/slices/appSlice.js) — fields: `loading.status`, `loading.message`, `stepperDisable`, `triggerInstallOnce`

`userSlice`  (src/redux/slices/userSlice.js) — fields: `mobile`, `requestId`, `customer`, `lead`, `employment`, `accountId`, `selectedLoanOffer`, `hasLoanOffer`, `upgradeLoanAmount`, `month12Clicked`, `isNewDigilocker`

**LocalStorage keys** (src/utils/storage.js) — `KEYS` object; specific key names unclear from source (skeletonized), but includes: `JWT_TOKEN`, `ACCESS_TOKEN`, `LEAD_ID` (referenced in service file comments)

**i18n locale schemas** (src/i18n/locales/en.json, hi.json, ka.json) — Not DB models; UI string maps for English, Hindi, Kannada. Keys cover: `login`, `panVerify`, `employmentDetails`, `selectLoanOffer`, `loanApproval`, `yourEmail`, `aadhaarVerification`, `cameraPermission`, `selfie`, `addBankAccount`, `pennyDrop`, `kfs`, `disbursed`, `loanRejected`, `finboxError`, `loaderMsg`, plus validation namespaces.

## onboarding-service

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

## onboarding_service_frontend

This is a pure frontend SPA with no direct database. State is persisted via redux-persist to `localStorage`.

**In-Memory / Redux (persisted to localStorage via redux-persist)**

`AppState  (src/redux/slices/appSlice.js)`
— fields: loading.status, loading.message, stepperDisable, triggerInstallOnce
— relationships: none

`UserState  (src/redux/slices/userSlice.js)`
— fields: mobile, requestId, customer (object), lead (object), employment (object), accountId, selectedLoanOffer (object), hasLoanOffer, upgradeLoanAmount, month12Clicked, isNewDigilocker
— relationships: selectedLoanOffer references lead and product IDs

**localStorage Keys  (src/utils/storage.js)**
— KEYS constants include: JWT_TOKEN, ACCESS_TOKEN, LEAD_ID, CUSTOMER_ID (and others; full list unclear from skeletonized source)
— Format: JSON-serialized values via `Storage.set/get`

**API Contract Shapes (inferred from service call parameters in `src/services/userService.js`)**

`CustomerLogin  (userService.js)`
— fields: mobile, options (UTM params)

`VerifyOTP  (userService.js)`
— fields: request_id, otp, whatsapp_consent, consent, bankfetch_consent

`PANVerification  (userService.js)`
— fields: pan_number, pin_code, loan_purpose (passed to panVerificationAPI)

`PANConfirmation  (userService.js)`
— fields: panNumber

`BasicDetails  (userService.js)`
— fields: unclear from source (data object passed to basicDetailsAPI)

`EmploymentDetails  (userService.js)`
— fields: monthly_income, employment_type, income_mode, salary_date

`AddBankDetails  (userService.js)`
— fields: account_number, ifsc, previousAccountID

`GenerateAadhaarOTP  (userService.js)`
— fields: aadhar_no, account_id

`VerifyAadhaarOTP  (userService.js)`
— fields: aadhar_no, otp, account_id

`LoanApprovalView  (userService.js)`
— fields: data object (unclear full shape)

`KeyfactsAcceptance  (userService.js)`
— fields: latitude, longitude

`InitiateCKYC  (userService.js)`
— fields: unclear from source

`VerifyCKYC  (userService.js)`
— fields: transaction_id, otp

`EventsFunnel  (userService.js)`
— fields: eventName, attributes (object)

## onboarding_service_frontend.raw

This is a pure frontend SPA with no direct database. State is persisted via redux-persist to `localStorage`.

**In-Memory / Redux (persisted to localStorage via redux-persist)**

`AppState  (src/redux/slices/appSlice.js)`
— fields: loading.status, loading.message, stepperDisable, triggerInstallOnce
— relationships: none

`UserState  (src/redux/slices/userSlice.js)`
— fields: mobile, requestId, customer (object), lead (object), employment (object), accountId, selectedLoanOffer (object), hasLoanOffer, upgradeLoanAmount, month12Clicked, isNewDigilocker
— relationships: selectedLoanOffer references lead and product IDs

**localStorage Keys  (src/utils/storage.js)**
— KEYS constants include: JWT_TOKEN, ACCESS_TOKEN, LEAD_ID, CUSTOMER_ID (and others; full list unclear from skeletonized source)
— Format: JSON-serialized values via `Storage.set/get`

**API Contract Shapes (inferred from service call parameters in `src/services/userService.js`)**

`CustomerLogin  (userService.js)`
— fields: mobile, options (UTM params)

`VerifyOTP  (userService.js)`
— fields: request_id, otp, whatsapp_consent, consent, bankfetch_consent

`PANVerification  (userService.js)`
— fields: pan_number, pin_code, loan_purpose (passed to panVerificationAPI)

`PANConfirmation  (userService.js)`
— fields: panNumber

`BasicDetails  (userService.js)`
— fields: unclear from source (data object passed to basicDetailsAPI)

`EmploymentDetails  (userService.js)`
— fields: monthly_income, employment_type, income_mode, salary_date

`AddBankDetails  (userService.js)`
— fields: account_number, ifsc, previousAccountID

`GenerateAadhaarOTP  (userService.js)`
— fields: aadhar_no, account_id

`VerifyAadhaarOTP  (userService.js)`
— fields: aadhar_no, otp, account_id

`LoanApprovalView  (userService.js)`
— fields: data object (unclear full shape)

`KeyfactsAcceptance  (userService.js)`
— fields: latitude, longitude

`InitiateCKYC  (userService.js)`
— fields: unclear from source

`VerifyCKYC  (userService.js)`
— fields: transaction_id, otp

`EventsFunnel  (userService.js)`
— fields: eventName, attributes (object)

## ramfin-report

### MySQL (Knex, primary + read replica)

`IAddress  (src/interfaces/address.interface.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy`

`IApiReqResLog  (src/interfaces/api_req_res_log.interface.ts)  — fields: id, customerID, mobile, api_request, api_response, created_at, status, message, api_name`

`IApproval  (src/interfaces/approval.interface.ts)  — fields: approvalID, customerID, leadID, loanType, productType, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, plateFormFee, convinineceFee, creditRiskAnalisys, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, activeLoans, outstandingAmount, monthlyObligation, status, formNo, employed, remark, loanRequirePurpose, creditedBy, rejectionReason, redFlag, createdDate, sanctionalloUID, customerApproval, employmentType, m1-m3, m_avg, p1-p3, m1_date-m3_date, disbursalRemark`

`IAutoDisbursalLogsModel  (src/interfaces/auto_disbursal_logs.interface.ts)  — fields: id, customerID, leadID, api_request, api_response, userID, any_error, status, createdDate`

`ICallHistoryLog  (src/interfaces/callhistorylogs.interface.ts)  — fields: callHistoryID, customerID, leadID, callType, status, appAmount, noteli, remark, callbackTime, calledBy, createdDate`

`ICollection  (src/interfaces/collection.interface.ts)  — fields: collectionID, customerID, leadID, loanNo, collectedAmount, penaltyAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, createdDate, collectionStatus, collectionStatusby, approvedDate, orderID, excess_amount, discount_waiver, discount_waiver_amount, refund_utr_no, opening_balance, closing_balance, total_interest, principal_amount, penality_charge, collected_interest, collected_principal, collected_penality, updated_date, collectedDateIST, refundType, refundRemarks, approvedBy, amount, mode, remarks`

`ICredit  (src/interfaces/credit.interface.ts)  — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, actualTenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, paneltyEmis, status, principal, amountToBeRepayed, firstDueDate, brokenPeriodIntrest, gst, created_at, disbursalDate`

`ICustomer  (src/interfaces/customer.interface.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, step, ckyc_status`

`ICustomerAccount  (src/interfaces/customerAccount.interface.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, createdDate, bank_holder_name, is_credit`

`IDisbursalJobsModel  (src/interfaces/disbursalJobs.interface.ts)  — fields: id, customerID, leadID, loanID, loanNo, accountNo, ifsc, actualDisbAmount, custName, custMobile, custEmail, companyAcc, userID, createdDate, currentStatus, jobStatus, apiStatus`

`IEmi  (src/interfaces/emi.interface.ts)  — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paneltyID, paymentID, status, amountRemains, amountRemainsInterest, amountRemainsPenalty, amountRemainsBrokenPeriodIntrest, brokenPeriodIntrest, accessAmount, paymentReceived, is_deleted, waive_off_amount`

`ILeadsApiLog  (src/interfaces/lead_api_log.interface.ts)  — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo, code, state, entity_id, sync_id, sync_result, sync_data, amount`

`ILead  (src/interfaces/lead.interface.ts)  — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, ip, callAssign, creditAssign, createdDate, alloUID, sanctionalloUID, step, kfs, productID, ipc, hold_date, lenderID`

`ILoan  (src/interfaces/loan.interface.ts)  — fields: loanID, leadID, lenderID, loanNo, customerID, approvalID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, accountNo, accountType, bankIfsc, bank, bankBranch, chequeDetails, pdDate, pdDoneBy, repayDate, deduction, remarks, status, rejReason, companyAccountNo, ip, disbursedBy, createdDate, allocate_date, allocated_by, is_manual, manual_date, utr, payout_status, cooling_period_flag, cooling_period_date`

`IMailTemplate  (src/interfaces/mailTemplate.interface.ts)  — fields: id, name, subject, message`

`INotification  (src/interfaces/notification.interface.ts)  — fields: notificationID, customerID, leadID, notification, type, subject, createdDate, mtype, uid`

`IReportDownloadLog  (src/database/mysql/report_download_log.ts)  — fields: id, user_id, procedure_name, file_type, status (PENDING|COMPLETED|FAILED), s3_url, error_message, created_at, updated_at`

`IRole  (src/interfaces/roles.interface.ts)  — fields: role_id, role_name, role_display_name, status, created_at, created_by, updated_at, updated_by`

`ISwitchThirdPartyApiModel  (src/interfaces/switchThirdPartyApi.interface.ts)  — fields: id, api_type, vendor, status, failed_count`

`ITransection  (src/interfaces/transections.interface.ts)  — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, deleted, gateway, createdAt, updatedAt, createdBy, updatedBy, amount, collectionID, emiID, transactionDate, remarks, payment_transaction_status, waiver, discount_type`

`IUser  (src/interfaces/users.interface.ts)  — fields: userID, name, email, mobile, did_no, branch, userName, password, role, status, createdBy, createdDate, accessPer, utype, firebase_token, device_token, lip, convoque_login_id, convoque_exten, whatsapp_email, lead_status, otp, password_updated_at, mac_address, random_id, mac_otp, utmSource`

`IWaiver  (src/interfaces/waiver.interface.ts)  — fields: id, lead_id, customer_id, collection_id, emi_id, credit_id, amount, product, expiration_time, type, remarks, is_paid, status, created_by, updated_by, created_at, updated_at, approved_date`

`IWhitelistIP  (src/interfaces/users.interface.ts)  — fields: id, ip, status`

### MongoDB (Mongoose)

`OtpLogs  (src/database/mongo/OtpLogs.ts)  — fields: customerID, mobile, req_url, api_request, api_response, curl_error, created_at, type, iu_date, platform`

### AWS S3 (file storage, no ORM model)

Report files (xlsx, csv, txt) uploaded via `S3Service.uploadSQSDocument` / `uploadReportFile` to bucket configured in `aws_s3_bucket_name` / `awsSQSS3Bucket`; presigned URLs generated via `getSignedReportUrl`.

## ramfin-report.raw

### MySQL (Knex, primary + read replica)

`IAddress  (src/interfaces/address.interface.ts)  — fields: addressID, customerID, type, address, city, state, pincode, status, verifiedBy, createdDate, address2, landmark, area, region, fetchedBy`

`IApiReqResLog  (src/interfaces/api_req_res_log.interface.ts)  — fields: id, customerID, mobile, api_request, api_response, created_at, status, message, api_name`

`IApproval  (src/interfaces/approval.interface.ts)  — fields: approvalID, customerID, leadID, loanType, productType, branch, loanAmtApproved, tenure, roi, repayDate, adminFee, plateFormFee, convinineceFee, creditRiskAnalisys, GstOfAdminFee, alternateMobile, officialEmail, monthlyIncome, cibil, activeLoans, outstandingAmount, monthlyObligation, status, formNo, employed, remark, loanRequirePurpose, creditedBy, rejectionReason, redFlag, createdDate, sanctionalloUID, customerApproval, employmentType, m1-m3, m_avg, p1-p3, m1_date-m3_date, disbursalRemark`

`IAutoDisbursalLogsModel  (src/interfaces/auto_disbursal_logs.interface.ts)  — fields: id, customerID, leadID, api_request, api_response, userID, any_error, status, createdDate`

`ICallHistoryLog  (src/interfaces/callhistorylogs.interface.ts)  — fields: callHistoryID, customerID, leadID, callType, status, appAmount, noteli, remark, callbackTime, calledBy, createdDate`

`ICollection  (src/interfaces/collection.interface.ts)  — fields: collectionID, customerID, leadID, loanNo, collectedAmount, penaltyAmount, collectedMode, collectedDate, referenceNo, discountAmount, settlemenAmount, status, remark, collectedBy, createdDate, collectionStatus, collectionStatusby, approvedDate, orderID, excess_amount, discount_waiver, discount_waiver_amount, refund_utr_no, opening_balance, closing_balance, total_interest, principal_amount, penality_charge, collected_interest, collected_principal, collected_penality, updated_date, collectedDateIST, refundType, refundRemarks, approvedBy, amount, mode, remarks`

`ICredit  (src/interfaces/credit.interface.ts)  — fields: creditID, customerID, leadID, productID, branch, foir, aqb, roi, tenure, actualTenure, interest, repaymentAmount, totalEMIs, emiLeft, processingFee, paidAmount, paneltyEmis, status, principal, amountToBeRepayed, firstDueDate, brokenPeriodIntrest, gst, created_at, disbursalDate`

`ICustomer  (src/interfaces/customer.interface.ts)  — fields: customerID, name, firstName, middleName, lastName, gender, dob, mobile, email, pancard, aadharNo, password, marrital, profile, otp, isVerified, employeeType, createdDate, industry, designation, working_since, salary_date, official_email, education, pan_cust_verified, dob_digit_match, is_pan_aadhar_linked, is_dob_match, status, step, ckyc_status`

`ICustomerAccount  (src/interfaces/customerAccount.interface.ts)  — fields: accountID, leadID, customerID, accountNo, accountType, bankIfsc, bank, bankBranch, ip, credatedBy, status, createdDate, bank_holder_name, is_credit`

`IDisbursalJobsModel  (src/interfaces/disbursalJobs.interface.ts)  — fields: id, customerID, leadID, loanID, loanNo, accountNo, ifsc, actualDisbAmount, custName, custMobile, custEmail, companyAcc, userID, createdDate, currentStatus, jobStatus, apiStatus`

`IEmi  (src/interfaces/emi.interface.ts)  — fields: emiID, creditID, productID, leadID, customerID, principal, interest, panelty, amountPayable, openingBalance, closingBalance, dueDate, actualPaymentDate, delayDays, paneltyID, paymentID, status, amountRemains, amountRemainsInterest, amountRemainsPenalty, amountRemainsBrokenPeriodIntrest, brokenPeriodIntrest, accessAmount, paymentReceived, is_deleted, waive_off_amount`

`ILeadsApiLog  (src/interfaces/lead_api_log.interface.ts)  — fields: id, leadID, api_supplier, api_type, api_endpoint_url, api_headers, api_method, api_request, api_response, created_at, status, customerID, mobile_no, pancard, aadharNo, code, state, entity_id, sync_id, sync_result, sync_data, amount`

`ILead  (src/interfaces/lead.interface.ts)  — fields: leadID, customerID, userID, purpose, loanRequeried, tenure, monthlyIncome, salaryMode, city, state, pincode, status, utmSource, fbLeads, domainName, ip, callAssign, creditAssign, createdDate, alloUID, sanctionalloUID, step, kfs, productID, ipc, hold_date, lenderID`

`ILoan  (src/interfaces/loan.interface.ts)  — fields: loanID, leadID, lenderID, loanNo, customerID, approvalID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, accountNo, accountType, bankIfsc, bank, bankBranch, chequeDetails, pdDate, pdDoneBy, repayDate, deduction, remarks, status, rejReason, companyAccountNo, ip, disbursedBy, createdDate, allocate_date, allocated_by, is_manual, manual_date, utr, payout_status, cooling_period_flag, cooling_period_date`

`IMailTemplate  (src/interfaces/mailTemplate.interface.ts)  — fields: id, name, subject, message`

`INotification  (src/interfaces/notification.interface.ts)  — fields: notificationID, customerID, leadID, notification, type, subject, createdDate, mtype, uid`

`IReportDownloadLog  (src/database/mysql/report_download_log.ts)  — fields: id, user_id, procedure_name, file_type, status (PENDING|COMPLETED|FAILED), s3_url, error_message, created_at, updated_at`

`IRole  (src/interfaces/roles.interface.ts)  — fields: role_id, role_name, role_display_name, status, created_at, created_by, updated_at, updated_by`

`ISwitchThirdPartyApiModel  (src/interfaces/switchThirdPartyApi.interface.ts)  — fields: id, api_type, vendor, status, failed_count`

`ITransection  (src/interfaces/transections.interface.ts)  — fields: id, customerID, leadID, loanNo, status, type, mode, referenceNo, orderId, deleted, gateway, createdAt, updatedAt, createdBy, updatedBy, amount, collectionID, emiID, transactionDate, remarks, payment_transaction_status, waiver, discount_type`

`IUser  (src/interfaces/users.interface.ts)  — fields: userID, name, email, mobile, did_no, branch, userName, password, role, status, createdBy, createdDate, accessPer, utype, firebase_token, device_token, lip, convoque_login_id, convoque_exten, whatsapp_email, lead_status, otp, password_updated_at, mac_address, random_id, mac_otp, utmSource`

`IWaiver  (src/interfaces/waiver.interface.ts)  — fields: id, lead_id, customer_id, collection_id, emi_id, credit_id, amount, product, expiration_time, type, remarks, is_paid, status, created_by, updated_by, created_at, updated_at, approved_date`

`IWhitelistIP  (src/interfaces/users.interface.ts)  — fields: id, ip, status`

### MongoDB (Mongoose)

`OtpLogs  (src/database/mongo/OtpLogs.ts)  — fields: customerID, mobile, req_url, api_request, api_response, curl_error, created_at, type, iu_date, platform`

### AWS S3 (file storage, no ORM model)

Report files (xlsx, csv, txt) uploaded via `S3Service.uploadSQSDocument` / `uploadReportFile` to bucket configured in `aws_s3_bucket_name` / `awsSQSS3Bucket`; presigned URLs generated via `getSignedReportUrl`.

## ramfin_userservice

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

## ramfin_userservice.raw

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

## ramfincorp-backend

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

## ramfincorp-backend.raw

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

## ramfincorp-notification

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

## ramfincorp-notification.raw

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

## stored-procedure-RamFin

All models are MySQL tables (no ORM definitions present — inferred from procedure joins and column references).

### MySQL (`ramfin` database)

`customer`  (referenced throughout) — fields: customerID, name, mobile, email, dob, gender, pancard, aadharNo, employeeType, designation, createdDate — relationships: → leads, loan, collection, address, employer, reference

`leads`  (referenced throughout) — fields: leadID, customerID, fbLeads, status, productID, utmSource, utm_assigned_date, state, city, pincode, loanRequeried, monthlyIncome, purpose, createdDate, ipc, lenderID, alloUID — relationships: → loan, approval, collection, customer

`loan`  (referenced throughout) — fields: loanID, loanNo, leadID, customerID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, status, utr, payout_status, deduction, writeoff_status, writeoff_date, em_id, bankBranch, createdDate — relationships: → leads, approval, collection

`approval`  (referenced throughout) — fields: leadID, customerID, status, loanAmtApproved, roi, tenure, repayDate, adminFee, GstOfAdminFee, branch, creditedby, sanctionalloUID, rejectionReason, createdDate, loanType — relationships: → loan, leads, users

`collection`  (referenced throughout) — fields: collectionID, leadID, loanNo, customerID, collectedAmount, collectedDate, collectionStatus, status, collectedMode, referenceNo, orderID, remark, settlemenAmount, discountAmount, discount_waiver_amount, excess_amount, principal_amount, collected_principal, collected_interest, collected_penality, opening_balance, closing_balance, total_interest, penality_charge, closing_balance, createdDate — relationships: → loan, leads

`equated_monthly_installments`  (referenced in EMI procedures) — fields: emiID, leadID, status, dueDate, principal, interest, panelty, amountPayable, paymentReceived, amountRemains, amountRemainsInterest, amountRemainsPenalty, amountRemainsBrokenPeriodIntrest, waive_off_amount, actualPaymentDate, is_deleted, accessAmount, createdAt — relationships: → leads, loan

`transactions`  (referenced in collection_emi_data, get_loan_book_data_withemi) — fields: id, leadID, loanNo, customerID, amount, status, mode, gateway, orderId, referenceNo, transactionDate, createdAt, updatedAt, waiver, remarks, type, emiID — relationships: → emi_transactions

`emi_transactions`  (referenced in collection_emi_data, get_loan_book_data_withemi) — fields: id, transaction_id, emi_id, principal, interest, penalty, dpd_amount, emi_status — relationships: → transactions, equated_monthly_installments

`credits`  (referenced in EMI procedures) — fields: leadID, customerID, tenure, roi — relationships: → leads

`users`  (referenced throughout) — fields: userID, name, email, mobile, utmSource, referralCode, status, createdDate — relationships: → approval, callhistoryLogs

`callhistoryLogs`  (referenced throughout) — fields: callHistoryID, leadID, customerID, calledBy, status, callType, callbackTime, createdDate — relationships: → users, leads

`collectionFollowup`  (referenced in account procedures) — fields: reviewID, leadID, customerID, followType, statusType, statusTypeDate, remark, createdDate

`address`  (referenced in multiple procedures) — fields: customerID, address, city, state, pincode, landmark, type

`employer`  (referenced in pending reports) — fields: customerID, employerName, empEmail, empDesignation, address, city, state, pincode

`reference`  (referenced in pending reports) — fields: referenceID, customerID, name, relation, contactNo, reference_verify

`eventLogs`  (referenced in funnel reports) — fields: id, customerId, eventName, eventDate, utmSource, userType, leadId, platformVersion

`user_flow_data`  (referenced in user_funnel, event_data) — fields: customerID, event_type, event_date

`journey_logs`  (referenced in api_log_data_with_error, get_journey_logs) — fields: api_name, status, message, createdDate

`user_attributions`  (referenced in DSA procedures) — fields: id, customerID, source, medium, campaign, trackingid, expiryDate, createdDate

`user_utm_link`  (referenced in DSA procedures) — fields: user_id, utm_source, dsa_name

`onlinepayment`  (referenced in collection dashboard) — fields: pID, razorpayOrderId, razorpayPaymentId, method

`lender`  (referenced in collection/pending procedures) — fields: lenderID, name

`leads_api_log`  (referenced in cibil_data_dump) — fields: mobile_no, api_type, api_response, status

`customerApp`  (referenced in NotCompletedReport, leads_not_completed_status_report_data) — fields: customerID, step, name, mobile, email, loanRequeried, monthlyIncome, city, pincode, utmSource, createdDate

`cibil_score`  (referenced in loan book procedures) — fields: customerID, score

`credit_reports`  (referenced in loan book procedures) — fields: customerID, score

`razorpay_mandate`  (referenced in get_lead_data) — fields: id, status, credated_date

`penny_drop`  (referenced in get_lead_data) — fields: customerID, credated_date

`encryption_keys`  (referenced in payday_pending_report, payday_pending_emi_report) — fields: key_name, secret_key, iv, is_active

`customer_dnd`  (referenced in payday_pending_emi_report) — fields: id, customerID, expiry_date, is_deleted

`razorpay_payout_disbured_amount`  (referenced in loan book procedures) — fields: leadID, status

`login_device_detail`  (referenced in NotCompletedReport) — fields: mobile, modelName, android_version

`temp_report_results` / `temp_report_results1`  (in-memory/session tables, used in collection_summary variants) — fields: row_order, type_name, no_of_cases_1, loan_amount, loan_percentage, no_of_cases_2, repay_date_amount, collection_amount, collection_percentage

`loanbook{YYYYMMDD}`  (dynamically created/named tables) — fields: all loan book columns including Disbursal Amount, PF, Loan_POS, WriteOffFlag, WriteOffDate, Collected Month, Principal Collected_ipc, Interest Collected_ipc, Late Fee Collected_ipc, etc. — created by `get_loan_book_data_withemi`; read by `get_loan_book_data_withemi_static*`, `GetLoanbookSummaryRange`, `fy_monthly_summary`

### MySQL (`dsa` schema — cross-database)

`dsa.users`  — fields: id, internal_user_id, utm_code, email — relationships: → ramfin.users via internal_user_id

`dsa.commission_slab`  — fields: start, end, value, profile_id

`dsa.profile`  — fields: id, user_id

## stored-procedure-RamFin.raw

All models are MySQL tables (no ORM definitions present — inferred from procedure joins and column references).

### MySQL (`ramfin` database)

`customer`  (referenced throughout) — fields: customerID, name, mobile, email, dob, gender, pancard, aadharNo, employeeType, designation, createdDate — relationships: → leads, loan, collection, address, employer, reference

`leads`  (referenced throughout) — fields: leadID, customerID, fbLeads, status, productID, utmSource, utm_assigned_date, state, city, pincode, loanRequeried, monthlyIncome, purpose, createdDate, ipc, lenderID, alloUID — relationships: → loan, approval, collection, customer

`loan`  (referenced throughout) — fields: loanID, loanNo, leadID, customerID, disbursalAmount, disbursalDate, disbursalTime, disbursalRefrenceNo, status, utr, payout_status, deduction, writeoff_status, writeoff_date, em_id, bankBranch, createdDate — relationships: → leads, approval, collection

`approval`  (referenced throughout) — fields: leadID, customerID, status, loanAmtApproved, roi, tenure, repayDate, adminFee, GstOfAdminFee, branch, creditedby, sanctionalloUID, rejectionReason, createdDate, loanType — relationships: → loan, leads, users

`collection`  (referenced throughout) — fields: collectionID, leadID, loanNo, customerID, collectedAmount, collectedDate, collectionStatus, status, collectedMode, referenceNo, orderID, remark, settlemenAmount, discountAmount, discount_waiver_amount, excess_amount, principal_amount, collected_principal, collected_interest, collected_penality, opening_balance, closing_balance, total_interest, penality_charge, closing_balance, createdDate — relationships: → loan, leads

`equated_monthly_installments`  (referenced in EMI procedures) — fields: emiID, leadID, status, dueDate, principal, interest, panelty, amountPayable, paymentReceived, amountRemains, amountRemainsInterest, amountRemainsPenalty, amountRemainsBrokenPeriodIntrest, waive_off_amount, actualPaymentDate, is_deleted, accessAmount, createdAt — relationships: → leads, loan

`transactions`  (referenced in collection_emi_data, get_loan_book_data_withemi) — fields: id, leadID, loanNo, customerID, amount, status, mode, gateway, orderId, referenceNo, transactionDate, createdAt, updatedAt, waiver, remarks, type, emiID — relationships: → emi_transactions

`emi_transactions`  (referenced in collection_emi_data, get_loan_book_data_withemi) — fields: id, transaction_id, emi_id, principal, interest, penalty, dpd_amount, emi_status — relationships: → transactions, equated_monthly_installments

`credits`  (referenced in EMI procedures) — fields: leadID, customerID, tenure, roi — relationships: → leads

`users`  (referenced throughout) — fields: userID, name, email, mobile, utmSource, referralCode, status, createdDate — relationships: → approval, callhistoryLogs

`callhistoryLogs`  (referenced throughout) — fields: callHistoryID, leadID, customerID, calledBy, status, callType, callbackTime, createdDate — relationships: → users, leads

`collectionFollowup`  (referenced in account procedures) — fields: reviewID, leadID, customerID, followType, statusType, statusTypeDate, remark, createdDate

`address`  (referenced in multiple procedures) — fields: customerID, address, city, state, pincode, landmark, type

`employer`  (referenced in pending reports) — fields: customerID, employerName, empEmail, empDesignation, address, city, state, pincode

`reference`  (referenced in pending reports) — fields: referenceID, customerID, name, relation, contactNo, reference_verify

`eventLogs`  (referenced in funnel reports) — fields: id, customerId, eventName, eventDate, utmSource, userType, leadId, platformVersion

`user_flow_data`  (referenced in user_funnel, event_data) — fields: customerID, event_type, event_date

`journey_logs`  (referenced in api_log_data_with_error, get_journey_logs) — fields: api_name, status, message, createdDate

`user_attributions`  (referenced in DSA procedures) — fields: id, customerID, source, medium, campaign, trackingid, expiryDate, createdDate

`user_utm_link`  (referenced in DSA procedures) — fields: user_id, utm_source, dsa_name

`onlinepayment`  (referenced in collection dashboard) — fields: pID, razorpayOrderId, razorpayPaymentId, method

`lender`  (referenced in collection/pending procedures) — fields: lenderID, name

`leads_api_log`  (referenced in cibil_data_dump) — fields: mobile_no, api_type, api_response, status

`customerApp`  (referenced in NotCompletedReport, leads_not_completed_status_report_data) — fields: customerID, step, name, mobile, email, loanRequeried, monthlyIncome, city, pincode, utmSource, createdDate

`cibil_score`  (referenced in loan book procedures) — fields: customerID, score

`credit_reports`  (referenced in loan book procedures) — fields: customerID, score

`razorpay_mandate`  (referenced in get_lead_data) — fields: id, status, credated_date

`penny_drop`  (referenced in get_lead_data) — fields: customerID, credated_date

`encryption_keys`  (referenced in payday_pending_report, payday_pending_emi_report) — fields: key_name, secret_key, iv, is_active

`customer_dnd`  (referenced in payday_pending_emi_report) — fields: id, customerID, expiry_date, is_deleted

`razorpay_payout_disbured_amount`  (referenced in loan book procedures) — fields: leadID, status

`login_device_detail`  (referenced in NotCompletedReport) — fields: mobile, modelName, android_version

`temp_report_results` / `temp_report_results1`  (in-memory/session tables, used in collection_summary variants) — fields: row_order, type_name, no_of_cases_1, loan_amount, loan_percentage, no_of_cases_2, repay_date_amount, collection_amount, collection_percentage

`loanbook{YYYYMMDD}`  (dynamically created/named tables) — fields: all loan book columns including Disbursal Amount, PF, Loan_POS, WriteOffFlag, WriteOffDate, Collected Month, Principal Collected_ipc, Interest Collected_ipc, Late Fee Collected_ipc, etc. — created by `get_loan_book_data_withemi`; read by `get_loan_book_data_withemi_static*`, `GetLoanbookSummaryRange`, `fy_monthly_summary`

### MySQL (`dsa` schema — cross-database)

`dsa.users`  — fields: id, internal_user_id, utm_code, email — relationships: → ramfin.users via internal_user_id

`dsa.commission_slab`  — fields: start, end, value, profile_id

`dsa.profile`  — fields: id, user_id

