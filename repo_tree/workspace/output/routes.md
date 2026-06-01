# Routes & Endpoints Map

## DSA-Backend

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

## DSA-Backend.raw

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

## Kamakshimoney-onboarding

All routes are client-side React Router routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes:**
```
GET /                    ->  Login              (src/pages/Login.jsx)           — Mobile login + OTP
GET /auto-login          ->  AutoLogin          (src/pages/AutoLogin.jsx)       — Token-based auto login
GET /logout              ->  Logout             (src/pages/Logout.jsx)          — Clear session and redirect
GET /not-found           ->  NotFound           (src/pages/NotFound.jsx)        — 404 page
```

**Protected Routes (wrapped in ProtectedRoutes):**
```
GET /stepper                    ->  Stepper                (src/pages/Stepper.jsx)                — Step checker/redirect hub
GET /pan-verify                 ->  PANVerify              (src/pages/PANVerify.jsx)              — PAN + pincode + loan purpose entry
GET /employment-details         ->  EmploymentDetails      (src/pages/EmploymentDetails.jsx)      — Employment type, income, salary date
GET /select-tenure              ->  SelectTenure           (src/pages/SelectTenure.jsx)           — Loan offer/tenure selection
GET /loan-approval              ->  LoanApproval           (src/pages/LoanApproval.jsx)           — Loan offer confirmation
GET /your-email                 ->  YourEmail              (src/pages/YourEmail.jsx)              — Email collection + Google sign-in
GET /aadhaar-verification       ->  AadhaarVerification    (src/pages/AadhaarVerification.jsx)    — Aadhaar entry + OTP verify / Digilocker
GET /digilocker-verify          ->  DigilockerVerify       (src/pages/DigilockerVerify.jsx)       — Digilocker callback handler
GET /camera-permission          ->  CameraPermission       (src/pages/CameraPermission.jsx)       — Request camera access
GET /selfie-verification        ->  Selfie                 (src/pages/Selfie.jsx)                 — Webcam selfie + liveness check
GET /selfie-hyperverge          ->  SelfieHyperVerge       (src/pages/SelfieHyperVerge.jsx)       — HyperVerge selfie SDK flow
GET /selfie-hyperverge-result   ->  SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result handler
GET /add-bank-account           ->  AddBankAccount         (src/pages/AddBankAccount.jsx)         — Bank account entry form
GET /confirm-bank-account       ->  ConfirmBankAccount     (src/pages/ConfirmBankAccount.jsx)     — Bank account confirmation
GET /penny-drop                 ->  PennyDrop              (src/pages/PennyDrop.jsx)              — Penny drop verification
GET /emandate                   ->  Emandate               (src/pages/Emandate.jsx)               — E-mandate setup via Razorpay
GET /kfs                        ->  KFS                    (src/pages/KFS.jsx)                    — Key Facts Statement acceptance
GET /process-to-bank            ->  ProcessToBank          (src/pages/ProcessToBank.jsx)          — Processing/transition screen
GET /disbursed                  ->  Disbursed              (src/pages/Disbursed.jsx)              — Loan disbursement success
GET /loan-rejected              ->  LoanRejected           (src/pages/LoanRejected.jsx)           — Loan rejection screen
GET /finbox                     ->  Finbox                 (src/pages/Finbox.jsx)                 — Finbox bank statement link
GET /finbox-error               ->  FinboxError            (src/pages/FinboxError.jsx)            — Finbox error handler
GET /finbox-status              ->  FinboxStatus           (src/pages/FinboxStatus.jsx)           — Finbox connection status
```

---

## Kamakshimoney-onboarding.raw

All routes are client-side React Router routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes:**
```
GET /                    ->  Login              (src/pages/Login.jsx)           — Mobile login + OTP
GET /auto-login          ->  AutoLogin          (src/pages/AutoLogin.jsx)       — Token-based auto login
GET /logout              ->  Logout             (src/pages/Logout.jsx)          — Clear session and redirect
GET /not-found           ->  NotFound           (src/pages/NotFound.jsx)        — 404 page
```

**Protected Routes (wrapped in ProtectedRoutes):**
```
GET /stepper                    ->  Stepper                (src/pages/Stepper.jsx)                — Step checker/redirect hub
GET /pan-verify                 ->  PANVerify              (src/pages/PANVerify.jsx)              — PAN + pincode + loan purpose entry
GET /employment-details         ->  EmploymentDetails      (src/pages/EmploymentDetails.jsx)      — Employment type, income, salary date
GET /select-tenure              ->  SelectTenure           (src/pages/SelectTenure.jsx)           — Loan offer/tenure selection
GET /loan-approval              ->  LoanApproval           (src/pages/LoanApproval.jsx)           — Loan offer confirmation
GET /your-email                 ->  YourEmail              (src/pages/YourEmail.jsx)              — Email collection + Google sign-in
GET /aadhaar-verification       ->  AadhaarVerification    (src/pages/AadhaarVerification.jsx)    — Aadhaar entry + OTP verify / Digilocker
GET /digilocker-verify          ->  DigilockerVerify       (src/pages/DigilockerVerify.jsx)       — Digilocker callback handler
GET /camera-permission          ->  CameraPermission       (src/pages/CameraPermission.jsx)       — Request camera access
GET /selfie-verification        ->  Selfie                 (src/pages/Selfie.jsx)                 — Webcam selfie + liveness check
GET /selfie-hyperverge          ->  SelfieHyperVerge       (src/pages/SelfieHyperVerge.jsx)       — HyperVerge selfie SDK flow
GET /selfie-hyperverge-result   ->  SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result handler
GET /add-bank-account           ->  AddBankAccount         (src/pages/AddBankAccount.jsx)         — Bank account entry form
GET /confirm-bank-account       ->  ConfirmBankAccount     (src/pages/ConfirmBankAccount.jsx)     — Bank account confirmation
GET /penny-drop                 ->  PennyDrop              (src/pages/PennyDrop.jsx)              — Penny drop verification
GET /emandate                   ->  Emandate               (src/pages/Emandate.jsx)               — E-mandate setup via Razorpay
GET /kfs                        ->  KFS                    (src/pages/KFS.jsx)                    — Key Facts Statement acceptance
GET /process-to-bank            ->  ProcessToBank          (src/pages/ProcessToBank.jsx)          — Processing/transition screen
GET /disbursed                  ->  Disbursed              (src/pages/Disbursed.jsx)              — Loan disbursement success
GET /loan-rejected              ->  LoanRejected           (src/pages/LoanRejected.jsx)           — Loan rejection screen
GET /finbox                     ->  Finbox                 (src/pages/Finbox.jsx)                 — Finbox bank statement link
GET /finbox-error               ->  FinboxError            (src/pages/FinboxError.jsx)            — Finbox error handler
GET /finbox-status              ->  FinboxStatus           (src/pages/FinboxStatus.jsx)           — Finbox connection status
```

---

## crm-kamakshimoney-frontend

All routes are client-side (React Router v6), defined in `src/routes/Router.js`.

### Authentication
```
/login                    -> Login                      (pages/Authentication/Login.js) — Login page
/verify-otp               -> VerifyOTP                  (pages/Authentication/VerifyOTP.js) — OTP verification
/forgot-password          -> ForgotPassword             (pages/Authentication/ForgotPassword.js) — Forgot password
/change-password          -> ChangePassword             (pages/Authentication/ChangePassword.js) — Change password
/auto-login               -> AutoLogin                  (pages/Authentication/AutoLogin.jsx) — Token-based auto login
/logout                   -> Logout                     (pages/Authentication/Logout.js) — Logout
```

### Dashboard
```
/dashboard                -> Dashboard                  (pages/Dashboard/index.js) — Main dashboard
```

### Leads
```
/leads/all                -> AllLeads                   (pages/Leads/AllLeads/index.js) — All leads list
/leads/hot                -> HotLeads                   (pages/Leads/HotLeads/index.js) — Hot leads
/leads/credit             -> CreditLeads                (pages/Leads/CreditLeads/index.js) — Credit leads
/leads/sanction           -> SanctionLeads              (pages/Leads/SanctionLeads/index.js) — Sanction leads
```

### Customer Profile
```
/customer-profile/:leadID -> CustomerProfile            (pages/CustomerProfile/index.js) — Full customer profile
```

### Customers
```
/customers                -> Customers                  (pages/Customers/index.js) — Customer list
/customers/update         -> CustomerDetailsUpdate      (pages/Customers/customer-details-update/CustomerDetailsUpdate.js) — Update customer details
```

### Collection
```
/collection/pending       -> PendingCollection          (pages/Collection/PendingCollection/index.js) — Pending collections
/collection/closed        -> Closed                     (pages/Collection/Closed/index.js) — Closed collections
/collection/settled       -> Settled                    (pages/Collection/Settled/index.js) — Settled collections
/collection/part-paid     -> PartPaid                   (pages/Collection/PartPaid/index.js) — Part-paid collections
/collection/dnd           -> DNDCustomer                (pages/Collection/DNDCustomer/index.js) — DND customers
/collection/add-not-required -> AddNotRequired          (pages/Collection/AddNotRequired/index.js) — Add not required
/collection/waived-off    -> WaivedOff                  (pages/Collection/WaivedOff/index.js) — Waived off loans
/collection/bulk-emandate -> BulkEmandate               (pages/Collection/BulkEmandate/BulkEmandate.js) — Bulk e-mandate
/collection/payday-pending-emi -> PaydayPaymentPendingEmi (pages/Collection/PaydayPaymentPendingEmi/index.jsx) — Payday pending EMI
/collection/refund        -> Refund                     (pages/Collection/Refund/index.jsx) — Refund management
```

### Collection Manager
```
/collection-manager       -> CollectionManager          (pages/CollectionManager/collectionManager.js) — Collection manager main
/collection-manager/approval-pending -> ApprovalPending (pages/CollectionManager/ApprovalPending/index.js) — Approval pending
/collection-manager/approved -> Approved               (pages/CollectionManager/Approved/index.js) — Approved collections
/collection-manager/rejected -> Rejected               (pages/CollectionManager/Rejected/index.js) — Rejected collections
/collection-manager/bulk-upload -> BulkUpload          (pages/CollectionManager/BulkUpload/index.js) — Bulk upload
/collection-manager/online-payments -> OnlinePayments  (pages/CollectionManager/OnlinePayments/index.js) — Online payments
```

### Disbursal
```
/disbursal/bank-update    -> BankUpdate                 (pages/Disbursal/BankUpdate/index.js) — Bank update
/disbursal/bank-update-rejected -> BankUpdateRejected  (pages/Disbursal/BankUpdateRejected/index.js) — Bank update rejected
/disbursal/disbursed      -> Disbursed                  (pages/Disbursal/Disbursed/index.js) — Disbursed list
/disbursal/manual         -> ManualDisbursal            (pages/Disbursal/ManualDisbursal/index.js) — Manual disbursal upload
```

### CRM Management
```
/crm/users                -> Users                      (pages/CRMManagement/Users/index.js) — User list
/crm/users/add            -> UserListAdd                (pages/CRMManagement/UserListAdd/index.js) — Add user
/crm/users/update/:userID -> UserListUpdate             (pages/CRMManagement/UserListUpdate/index.js) — Update user
/crm/users/access         -> UserListAccess             (pages/CRMManagement/UserListAccess/index.js) — User report access
/crm/logins               -> Logins                     (pages/CRMManagement/Logins/index.js) — Login records
/crm/permissions          -> PermissionsList            (pages/CRMManagement/PermissionsList/index.js) — Permissions list
/crm/roles                -> RolesList                  (pages/CRMManagement/RolesList/index.js) — Roles list
/crm/have-permission      -> HavePermission             (pages/CRMManagement/HavePermission/index.js) — Role permissions mapping
/crm/ip-whitelisting      -> IPWhiteListing             (pages/CRMManagement/IPWhiteListing/index.js) — IP whitelist
/crm/sourcing-partners    -> SourcingPartners           (pages/CRMManagement/SourcingPartners/index.js) — Sourcing partners
/crm/dsa-partners         -> DSAPartners                (pages/CRMManagement/DSAPartner/index.jsx) — DSA partners
```

### Lead Actions
```
/lead-actions/repayment-date  -> RepaymentDateManager  (pages/LeadActions/RepaymentDateManager/index.js) — Repayment date change
/lead-actions/name-mismatch   -> NameMismatchManager   (pages/LeadActions/NameMismatchManager/index.js) — Name mismatch
/lead-actions/payment-mode    -> PaymentModeManager    (pages/LeadActions/PaymentModeManager/index.js) — Payment mode
/lead-actions/selfie-verification -> ManualSelfieVerification (pages/LeadActions/ManualSelfieVerification/index.jsx) — Selfie verification
/lead-actions/selfie-confirmation -> ManualSelfieConfirmation (pages/LeadActions/ManualSelfieConfirmation/index.jsx) — Selfie confirmation
```

### App Function Management
```
/app/holiday-list         -> Holiday                    (pages/AppFunctionManagement/HolidayList/index.js) — Holiday management
/app/auto-disbursal-status -> AutoDisbursalStatus       (pages/AppFunctionManagement/AutoDisbursalStatus/index.js) — Auto disbursal toggle
/app/repayment-gateway    -> RepaymentGatewayType       (pages/AppFunctionManagement/RepaymentGatewayType/index.js) — Gateway type
```

### Reports
```
/reports                  -> Report/QuickReportsWrapper  (pages/Reports/report.js) — Reports landing
/reports/quick            -> QuickReports               (pages/Reports/quickReports.js) — Quick reports
/reports/quick-download   -> QuickReportDownloadRequest (pages/Reports/quickReportDownloadRequest.jsx) — Download requests
/reports/all-leads        -> AllLeadReports             (pages/Reports/allLeadReports.js) — All lead reports
/reports/collection-data  -> CollectionDataReport       (pages/Reports/collectionDataReport.js) — Collection data
/reports/collection-emi   -> CollectionEmiDataReport    (pages/Reports/collectionEmiDataReport.js) — EMI collection data
/reports/collection-payment-mode -> CollectionPaymentMode (pages/Reports/collectionPaymentMode.js) — Payment mode report
/reports/disbursed        -> DisbursedReport            (pages/Reports/disbursedReport.js) — Disbursal report
/reports/disbursed-data   -> DisbursedDataReport        (pages/Reports/disbursedDataReport.js) — Disbursal data
/reports/disbursal-dashboard -> DisbursalReportDashboard (pages/Reports/disbursalReportDashboard.js) — Disbursal dashboard
/reports/date-wise-collection -> DateWiseCollectionReport (pages/Reports/dateWiseCollectionReport.js) — Date-wise collection
/reports/date-wise-lead   -> DateWiseLeadReport         (pages/Reports/dateWiseLeadReport.js) — Date-wise leads
/reports/payday-pending   -> PayDayPendingReport        (pages/Reports/payDayPendingReport.js) — Payday pending
/reports/refund           -> RefundReport               (pages/Reports/refundReport.js) — Refund report
/reports/customer-feedback -> CustomerFeedback          (pages/Reports/customerFeedback.js) — Customer feedback
/reports/landing-partner  -> LandingPartnerLeads        (pages/Reports/landingPartnerLeads.js) — Landing partner
/reports/app-issue        -> AppIssueListReport         (pages/Reports/appIssueListReport.js) — App issue report
/reports/credit-hod       -> CreditHODReport            (pages/Reports/CreditHODReport.jsx) — Credit HOD report
/reports/credit-modification -> CreditModificationReport (pages/Reports/CreditModificationReport.jsx) — Credit modification
/reports/event-funnel     -> EventFunnelReport          (pages/Reports/EventFunnelReport.js) — Event funnel
```

### Logs
```
/logs/api                 -> APILogs                    (pages/Logs/APILogs/index.js) — API logs
/logs/chat                -> ChatLogs                   (pages/Logs/ChatLogs/index.js) — Chat logs
/logs/dialer              -> DialerLogs                 (pages/Logs/DialerLogs/index.js) — Dialer logs
/logs/kaleyra             -> KaleyraLogs                (pages/Logs/KaleyraLogs/index.js) — Kaleyra logs
/logs/razorpay            -> RazorpayLogs               (pages/Logs/RazorpayLogs/index.js) — Razorpay logs
/logs/sendinblue          -> SendInBlueLogs             (pages/Logs/SendInBlueLogs/index.js) — SendInBlue logs
/logs/whatsapp            -> WhatsappLogs               (pages/Logs/WhatsappLogs/index.js) — WhatsApp logs
/logs/app-installations   -> AppInstallations           (pages/Logs/AppInstallations/index.js) — App install logs
```

### Other
```
/blacklist/customers      -> BlacklistCustomers         (pages/Blacklisted/BlacklistCustomers/index.js) — Blacklisted customers
/blacklist/pancard        -> BlacklistPancard           (pages/Blacklisted/BlacklistPancard/index.js) — Blacklisted PANs
/callback-request         -> CallbackRequest            (pages/CallbackRequest/index.js) — Callback requests
/cibil                    -> CibilData                  (pages/Cibil/CibilData/index.js) — CIBIL data
/collection-setting/settlement -> SettlementReport      (pages/CollectionSetting/SettlementReport/index.js) — Settlement report
/feedback                 -> Feedback                   (pages/Feedback/index.jsx) — Customer feedback
/*                        -> Error404                   (components/errors/Error404.js) — 404 page
```

---

## crm-kamakshimoney-frontend.raw

All routes are client-side (React Router v6), defined in `src/routes/Router.js`.

### Authentication
```
/login                    -> Login                      (pages/Authentication/Login.js) — Login page
/verify-otp               -> VerifyOTP                  (pages/Authentication/VerifyOTP.js) — OTP verification
/forgot-password          -> ForgotPassword             (pages/Authentication/ForgotPassword.js) — Forgot password
/change-password          -> ChangePassword             (pages/Authentication/ChangePassword.js) — Change password
/auto-login               -> AutoLogin                  (pages/Authentication/AutoLogin.jsx) — Token-based auto login
/logout                   -> Logout                     (pages/Authentication/Logout.js) — Logout
```

### Dashboard
```
/dashboard                -> Dashboard                  (pages/Dashboard/index.js) — Main dashboard
```

### Leads
```
/leads/all                -> AllLeads                   (pages/Leads/AllLeads/index.js) — All leads list
/leads/hot                -> HotLeads                   (pages/Leads/HotLeads/index.js) — Hot leads
/leads/credit             -> CreditLeads                (pages/Leads/CreditLeads/index.js) — Credit leads
/leads/sanction           -> SanctionLeads              (pages/Leads/SanctionLeads/index.js) — Sanction leads
```

### Customer Profile
```
/customer-profile/:leadID -> CustomerProfile            (pages/CustomerProfile/index.js) — Full customer profile
```

### Customers
```
/customers                -> Customers                  (pages/Customers/index.js) — Customer list
/customers/update         -> CustomerDetailsUpdate      (pages/Customers/customer-details-update/CustomerDetailsUpdate.js) — Update customer details
```

### Collection
```
/collection/pending       -> PendingCollection          (pages/Collection/PendingCollection/index.js) — Pending collections
/collection/closed        -> Closed                     (pages/Collection/Closed/index.js) — Closed collections
/collection/settled       -> Settled                    (pages/Collection/Settled/index.js) — Settled collections
/collection/part-paid     -> PartPaid                   (pages/Collection/PartPaid/index.js) — Part-paid collections
/collection/dnd           -> DNDCustomer                (pages/Collection/DNDCustomer/index.js) — DND customers
/collection/add-not-required -> AddNotRequired          (pages/Collection/AddNotRequired/index.js) — Add not required
/collection/waived-off    -> WaivedOff                  (pages/Collection/WaivedOff/index.js) — Waived off loans
/collection/bulk-emandate -> BulkEmandate               (pages/Collection/BulkEmandate/BulkEmandate.js) — Bulk e-mandate
/collection/payday-pending-emi -> PaydayPaymentPendingEmi (pages/Collection/PaydayPaymentPendingEmi/index.jsx) — Payday pending EMI
/collection/refund        -> Refund                     (pages/Collection/Refund/index.jsx) — Refund management
```

### Collection Manager
```
/collection-manager       -> CollectionManager          (pages/CollectionManager/collectionManager.js) — Collection manager main
/collection-manager/approval-pending -> ApprovalPending (pages/CollectionManager/ApprovalPending/index.js) — Approval pending
/collection-manager/approved -> Approved               (pages/CollectionManager/Approved/index.js) — Approved collections
/collection-manager/rejected -> Rejected               (pages/CollectionManager/Rejected/index.js) — Rejected collections
/collection-manager/bulk-upload -> BulkUpload          (pages/CollectionManager/BulkUpload/index.js) — Bulk upload
/collection-manager/online-payments -> OnlinePayments  (pages/CollectionManager/OnlinePayments/index.js) — Online payments
```

### Disbursal
```
/disbursal/bank-update    -> BankUpdate                 (pages/Disbursal/BankUpdate/index.js) — Bank update
/disbursal/bank-update-rejected -> BankUpdateRejected  (pages/Disbursal/BankUpdateRejected/index.js) — Bank update rejected
/disbursal/disbursed      -> Disbursed                  (pages/Disbursal/Disbursed/index.js) — Disbursed list
/disbursal/manual         -> ManualDisbursal            (pages/Disbursal/ManualDisbursal/index.js) — Manual disbursal upload
```

### CRM Management
```
/crm/users                -> Users                      (pages/CRMManagement/Users/index.js) — User list
/crm/users/add            -> UserListAdd                (pages/CRMManagement/UserListAdd/index.js) — Add user
/crm/users/update/:userID -> UserListUpdate             (pages/CRMManagement/UserListUpdate/index.js) — Update user
/crm/users/access         -> UserListAccess             (pages/CRMManagement/UserListAccess/index.js) — User report access
/crm/logins               -> Logins                     (pages/CRMManagement/Logins/index.js) — Login records
/crm/permissions          -> PermissionsList            (pages/CRMManagement/PermissionsList/index.js) — Permissions list
/crm/roles                -> RolesList                  (pages/CRMManagement/RolesList/index.js) — Roles list
/crm/have-permission      -> HavePermission             (pages/CRMManagement/HavePermission/index.js) — Role permissions mapping
/crm/ip-whitelisting      -> IPWhiteListing             (pages/CRMManagement/IPWhiteListing/index.js) — IP whitelist
/crm/sourcing-partners    -> SourcingPartners           (pages/CRMManagement/SourcingPartners/index.js) — Sourcing partners
/crm/dsa-partners         -> DSAPartners                (pages/CRMManagement/DSAPartner/index.jsx) — DSA partners
```

### Lead Actions
```
/lead-actions/repayment-date  -> RepaymentDateManager  (pages/LeadActions/RepaymentDateManager/index.js) — Repayment date change
/lead-actions/name-mismatch   -> NameMismatchManager   (pages/LeadActions/NameMismatchManager/index.js) — Name mismatch
/lead-actions/payment-mode    -> PaymentModeManager    (pages/LeadActions/PaymentModeManager/index.js) — Payment mode
/lead-actions/selfie-verification -> ManualSelfieVerification (pages/LeadActions/ManualSelfieVerification/index.jsx) — Selfie verification
/lead-actions/selfie-confirmation -> ManualSelfieConfirmation (pages/LeadActions/ManualSelfieConfirmation/index.jsx) — Selfie confirmation
```

### App Function Management
```
/app/holiday-list         -> Holiday                    (pages/AppFunctionManagement/HolidayList/index.js) — Holiday management
/app/auto-disbursal-status -> AutoDisbursalStatus       (pages/AppFunctionManagement/AutoDisbursalStatus/index.js) — Auto disbursal toggle
/app/repayment-gateway    -> RepaymentGatewayType       (pages/AppFunctionManagement/RepaymentGatewayType/index.js) — Gateway type
```

### Reports
```
/reports                  -> Report/QuickReportsWrapper  (pages/Reports/report.js) — Reports landing
/reports/quick            -> QuickReports               (pages/Reports/quickReports.js) — Quick reports
/reports/quick-download   -> QuickReportDownloadRequest (pages/Reports/quickReportDownloadRequest.jsx) — Download requests
/reports/all-leads        -> AllLeadReports             (pages/Reports/allLeadReports.js) — All lead reports
/reports/collection-data  -> CollectionDataReport       (pages/Reports/collectionDataReport.js) — Collection data
/reports/collection-emi   -> CollectionEmiDataReport    (pages/Reports/collectionEmiDataReport.js) — EMI collection data
/reports/collection-payment-mode -> CollectionPaymentMode (pages/Reports/collectionPaymentMode.js) — Payment mode report
/reports/disbursed        -> DisbursedReport            (pages/Reports/disbursedReport.js) — Disbursal report
/reports/disbursed-data   -> DisbursedDataReport        (pages/Reports/disbursedDataReport.js) — Disbursal data
/reports/disbursal-dashboard -> DisbursalReportDashboard (pages/Reports/disbursalReportDashboard.js) — Disbursal dashboard
/reports/date-wise-collection -> DateWiseCollectionReport (pages/Reports/dateWiseCollectionReport.js) — Date-wise collection
/reports/date-wise-lead   -> DateWiseLeadReport         (pages/Reports/dateWiseLeadReport.js) — Date-wise leads
/reports/payday-pending   -> PayDayPendingReport        (pages/Reports/payDayPendingReport.js) — Payday pending
/reports/refund           -> RefundReport               (pages/Reports/refundReport.js) — Refund report
/reports/customer-feedback -> CustomerFeedback          (pages/Reports/customerFeedback.js) — Customer feedback
/reports/landing-partner  -> LandingPartnerLeads        (pages/Reports/landingPartnerLeads.js) — Landing partner
/reports/app-issue        -> AppIssueListReport         (pages/Reports/appIssueListReport.js) — App issue report
/reports/credit-hod       -> CreditHODReport            (pages/Reports/CreditHODReport.jsx) — Credit HOD report
/reports/credit-modification -> CreditModificationReport (pages/Reports/CreditModificationReport.jsx) — Credit modification
/reports/event-funnel     -> EventFunnelReport          (pages/Reports/EventFunnelReport.js) — Event funnel
```

### Logs
```
/logs/api                 -> APILogs                    (pages/Logs/APILogs/index.js) — API logs
/logs/chat                -> ChatLogs                   (pages/Logs/ChatLogs/index.js) — Chat logs
/logs/dialer              -> DialerLogs                 (pages/Logs/DialerLogs/index.js) — Dialer logs
/logs/kaleyra             -> KaleyraLogs                (pages/Logs/KaleyraLogs/index.js) — Kaleyra logs
/logs/razorpay            -> RazorpayLogs               (pages/Logs/RazorpayLogs/index.js) — Razorpay logs
/logs/sendinblue          -> SendInBlueLogs             (pages/Logs/SendInBlueLogs/index.js) — SendInBlue logs
/logs/whatsapp            -> WhatsappLogs               (pages/Logs/WhatsappLogs/index.js) — WhatsApp logs
/logs/app-installations   -> AppInstallations           (pages/Logs/AppInstallations/index.js) — App install logs
```

### Other
```
/blacklist/customers      -> BlacklistCustomers         (pages/Blacklisted/BlacklistCustomers/index.js) — Blacklisted customers
/blacklist/pancard        -> BlacklistPancard           (pages/Blacklisted/BlacklistPancard/index.js) — Blacklisted PANs
/callback-request         -> CallbackRequest            (pages/CallbackRequest/index.js) — Callback requests
/cibil                    -> CibilData                  (pages/Cibil/CibilData/index.js) — CIBIL data
/collection-setting/settlement -> SettlementReport      (pages/CollectionSetting/SettlementReport/index.js) — Settlement report
/feedback                 -> Feedback                   (pages/Feedback/index.jsx) — Customer feedback
/*                        -> Error404                   (components/errors/Error404.js) — 404 page
```

---

## crm-react

All routes are client-side React Router v6, defined in `src/routes/Router.js` and `src/routes/AppRouter.js`. Exact path strings are not fully visible in the skeletonized source; names are inferred from the lazy-import comments.

### Authentication
- `/login`  →  `Login`  (src/pages/Authentication/Login.js)  — User login form
- `/verify-otp`  →  `VerifyOTP`  (src/pages/Authentication/VerifyOTP.js)  — OTP verification
- `/forgot-password`  →  `ForgotPassword`  (src/pages/Authentication/ForgotPassword.js)  — Forgot password
- `/change-password`  →  `ChangePassword`  (src/pages/Authentication/ChangePassword.js)  — Change password
- `/auto-login`  →  `AutoLogin`  (src/pages/Authentication/AutoLogin.jsx)  — Token-based auto login
- `/logout`  →  `Logout`  (src/pages/Authentication/Logout.js)  — Session logout

### Dashboard
- `/dashboard`  →  `Dashboard`  (src/pages/Dashboard/index.js)  — Main KPI dashboard

### Leads
- `/leads/all`  →  `AllLeads`  (src/pages/Leads/AllLeads/index.js)  — All leads list
- `/leads/credit`  →  `CreditLeads`  (src/pages/Leads/CreditLeads/index.js)  — Credit team leads
- `/leads/hot`  →  `HotLeads`  (src/pages/Leads/HotLeads/index.js)  — Hot leads
- `/leads/sanction`  →  `SanctionLeads`  (src/pages/Leads/SanctionLeads/index.js)  — Sanction leads

### Customer Profile
- `/customer-profile`  →  `CustomerProfile`  (src/pages/CustomerProfile/index.js)  — Full customer profile (tabbed)

### Customers
- `/customers`  →  `Customers`  (src/pages/Customers/index.js)  — Customer list
- `/customers/:id/update`  →  `CustomerDetailsUpdate`  (src/pages/Customers/customer-details-update/CustomerDetailsUpdate.js)  — Update customer details

### Collection
- `/collection/pending`  →  `PendingCollection`  (src/pages/Collection/PendingCollection/index.js)  — Pending collections
- `/collection/closed`  →  `Closed`  (src/pages/Collection/Closed/index.js)  — Closed collections
- `/collection/settled`  →  `Settled`  (src/pages/Collection/Settled/index.js)  — Settled collections
- `/collection/part-paid`  →  `PartPaid`  (src/pages/Collection/PartPaid/index.js)  — Part-paid collections
- `/collection/dnd-customer`  →  `DNDCustomer`  (src/pages/Collection/DNDCustomer/index.js)  — DND customer list
- `/collection/add-not-required`  →  `AddNotRequired`  (src/pages/Collection/AddNotRequired/index.js)  — Add-not-required list
- `/collection/bulk-emandate`  →  `BulkEmandate`  (src/pages/Collection/BulkEmandate/BulkEmandate.js)  — Bulk e-mandate upload
- `/collection/waived-off`  →  `WaivedOff`  (src/pages/Collection/WaivedOff/index.js)  — Waived-off loans
- `/collection/payday-payment-pending`  →  `PaydayPaymentPendingEmi`  (src/pages/Collection/PaydayPaymentPendingEmi/index.jsx)  — Payday pending EMI
- `/collection/refund`  →  `Refund`  (src/pages/Collection/Refund/index.jsx)  — Refund management (tabbed)

### Collection Manager
- `/collection-manager`  →  `CollectionManager`  (src/pages/CollectionManager/collectionManager.js)  — Collection manager wrapper
- `/collection-manager/approval-pending`  →  `ApprovalPending`  (src/pages/CollectionManager/ApprovalPending/index.js)  — Pending approvals
- `/collection-manager/approved`  →  `Approved`  (src/pages/CollectionManager/Approved/index.js)  — Approved entries
- `/collection-manager/rejected`  →  `Rejected`  (src/pages/CollectionManager/Rejected/index.js)  — Rejected entries
- `/collection-manager/online-payments`  →  `OnlinePayments`  (src/pages/CollectionManager/OnlinePayments/index.js)  — Online payments
- `/collection-manager/bulk-upload`  →  `BulkUpload`  (src/pages/CollectionManager/BulkUpload/index.js)  — Bulk upload

### Collection Setting
- `/collection-setting/settlement-report`  →  `SettlementReport`  (src/pages/CollectionSetting/SettlementReport/index.js)  — Settlement report

### Disbursal
- `/disbursal/bank-update`  →  `BankUpdate`  (src/pages/Disbursal/BankUpdate/index.js)  — Bank update queue
- `/disbursal/bank-update-rejected`  →  `BankUpdateRejected`  (src/pages/Disbursal/BankUpdateRejected/index.js)  — Rejected bank updates
- `/disbursal/disbursed`  →  `Disbursed`  (src/pages/Disbursal/Disbursed/index.js)  — Disbursed loans
- `/disbursal/manual`  →  `ManualDisbursal`  (src/pages/Disbursal/ManualDisbursal/index.js)  — Manual disbursal upload

### CRM Management
- `/crm/users`  →  `Users`  (src/pages/CRMManagement/Users/index.js)  — User list
- `/crm/users/add`  →  `UserListAdd`  (src/pages/CRMManagement/UserListAdd/index.js)  — Add user
- `/crm/users/:userID/update`  →  `UserListUpdate`  (src/pages/CRMManagement/UserListUpdate/index.js)  — Update user
- `/crm/users/access`  →  `UserListAccess`  (src/pages/CRMManagement/UserListAccess/index.js)  — Manage report access
- `/crm/logins`  →  `Logins`  (src/pages/CRMManagement/Logins/index.js)  — Login history
- `/crm/ip-whitelisting`  →  `IPWhiteListing`  (src/pages/CRMManagement/IPWhiteListing/index.js)  — IP whitelist
- `/crm/permissions`  →  `PermissionsList`  (src/pages/CRMManagement/PermissionsList/index.js)  — Permissions list
- `/crm/roles`  →  `RolesList`  (src/pages/CRMManagement/RolesList/index.js)  — Roles list
- `/crm/roles/permissions`  →  `HavePermission`  (src/pages/CRMManagement/HavePermission/index.js)  — Role-permission mapping
- `/crm/sourcing-partners`  →  `SourcingPartners`  (src/pages/CRMManagement/SourcingPartners/index.js)  — Sourcing partners
- `/crm/dsa-partners`  →  `DSAPartners`  (src/pages/CRMManagement/DSAPartner/index.jsx)  — DSA partners

### App Function Management
- `/app/auto-disbursal-status`  →  `AutoDisbursalStatus`  (src/pages/AppFunctionManagement/AutoDisbursalStatus/index.js)  — Toggle auto disbursal
- `/app/holiday-list`  →  `Holiday`  (src/pages/AppFunctionManagement/HolidayList/index.js)  — Holiday management
- `/app/repayment-gateway-type`  →  `RepaymentGatewayType`  (src/pages/AppFunctionManagement/RepaymentGatewayType/index.js)  — Gateway type config

### Lead Actions
- `/lead-actions/manual-selfie-verification`  →  `ManualSelfieVerification`  (src/pages/LeadActions/ManualSelfieVerification/index.jsx)  — Selfie verification queue
- `/lead-actions/manual-selfie-confirmation`  →  `ManualSelfieConfirmation`  (src/pages/LeadActions/ManualSelfieConfirmation/index.jsx)  — Selfie confirmation
- `/lead-actions/name-mismatch`  →  `NameMismatchManager`  (src/pages/LeadActions/NameMismatchManager/index.js)  — Name mismatch resolution
- `/lead-actions/payment-mode`  →  `PaymentModeManager`  (src/pages/LeadActions/PaymentModeManager/index.js)  — Payment mode management
- `/lead-actions/repayment-date`  →  `RepaymentDateManager`  (src/pages/LeadActions/RepaymentDateManager/index.js)  — Repayment date changes

### Reports
- `/reports`  →  `Report`  (src/pages/Reports/report.js)  — Reports landing
- `/reports/quick`  →  `QuickReportsWrapper`  (src/pages/Reports/quickReportsWrapper.js)  — Quick report selector
- `/reports/quick-download`  →  `QuickReportDownloadRequest`  (src/pages/Reports/quickReportDownloadRequest.jsx)  — Download request queue
- `/reports/all-leads`  →  `AllLeadReports`  (src/pages/Reports/allLeadReports.js)  — All-leads report
- `/reports/date-wise-collection`  →  `DateWiseCollectionReport`  (src/pages/Reports/dateWiseCollectionReport.js)  — Date-wise collection
- `/reports/date-wise-lead`  →  `DateWiseLeadReport`  (src/pages/Reports/dateWiseLeadReport.js)  — Date-wise lead
- `/reports/disbursed`  →  `DisbursedReport`  (src/pages/Reports/disbursedReport.js)  — Disbursed report
- `/reports/disbursed-data`  →  `DisbursedDataReport`  (src/pages/Reports/disbursedDataReport.js)  — Disbursed data
- `/reports/disbursal-dashboard`  →  `DisbursalReportDashboard`  (src/pages/Reports/disbursalReportDashboard.js)  — Disbursal dashboard
- `/reports/collection-data`  →  `CollectionDataReport`  (src/pages/Reports/collectionDataReport.js)  — Collection data
- `/reports/collection-emi`  →  `CollectionEmiDataReport`  (src/pages/Reports/collectionEmiDataReport.js)  — Collection EMI data
- `/reports/collection-payment-mode`  →  `CollectionPaymentMode`  (src/pages/Reports/collectionPaymentMode.js)  — Payment mode report
- `/reports/payday-pending`  →  `PayDayPendingReport`  (src/pages/Reports/payDayPendingReport.js)  — Payday pending
- `/reports/customer-feedback`  →  `CustomerFeedback`  (src/pages/Reports/customerFeedback.js)  — Customer feedback
- `/reports/landing-partner-leads`  →  `LandingPartnerLeads`  (src/pages/Reports/landingPartnerLeads.js)  — Landing partner leads
- `/reports/app-issue-list`  →  `AppIssueListReport`  (src/pages/Reports/appIssueListReport.js)  — App issue list
- `/reports/refund`  →  `RefundReport`  (src/pages/Reports/refundReport.js)  — Refund report
- `/reports/credit-hod`  →  `CreditHODReport`  (src/pages/Reports/CreditHODReport.jsx)  — Credit HOD report
- `/reports/credit-modification`  →  `CreditModificationReport`  (src/pages/Reports/CreditModificationReport.jsx)  — Credit modification
- `/reports/event-funnel`  →  `EventFunnelReport`  (src/pages/Reports/EventFunnelReport.js)  — Event funnel
- `/reports/failed-loan-onboarding`  →  `FailedLoanOnboardingReport`  (src/pages/Reports/FailedLoanOnboardingReport.js)  — Failed onboarding

### Logs
- `/logs/api`  →  `APILogs`  (src/pages/Logs/APILogs/index.js)  — API call logs
- `/logs/app-installations`  →  `AppInstallations`  (src/pages/Logs/AppInstallations/index.js)  — App install logs
- `/logs/chat`  →  `ChatLogs`  (src/pages/Logs/ChatLogs/index.js)  — Chat logs
- `/logs/dialer`  →  `DialerLogs`  (src/pages/Logs/DialerLogs/index.js)  — Dialer logs
- `/logs/kaleyra`  →  `KaleyraLogs`  (src/pages/Logs/KaleyraLogs/index.js)  — Kaleyra logs
- `/logs/razorpay`  →  `RazorpayLogs`  (src/pages/Logs/RazorpayLogs/index.js)  — Razorpay logs
- `/logs/sendinblue`  →  `SendInBlueLogs`  (src/pages/Logs/SendInBlueLogs/index.js)  — SendInBlue logs
- `/logs/whatsapp`  →  `WhatsappLogs`  (src/pages/Logs/WhatsappLogs/index.js)  — WhatsApp logs

### Blacklisted
- `/blacklisted/customers`  →  `BlacklistCustomers`  (src/pages/Blacklisted/BlacklistCustomers/index.js)  — Blacklisted customers
- `/blacklisted/pancard`  →  `BlacklistPancard`  (src/pages/Blacklisted/BlacklistPancard/index.js)  — Blacklisted PANs

### Miscellaneous
- `/cibil`  →  `CibilData`  (src/pages/Cibil/CibilData/index.js)  — CIBIL data
- `/callback-request`  →  `CallbackRequest`  (src/pages/CallbackRequest/index.js)  — Callback requests
- `/feedback`  →  `Feedback`  (src/pages/Feedback/index.jsx)  — Customer feedback list
- `/secure-decryption`  →  `SecureDecryption`  (src/pages/SecureDecryption/index.jsx)  — Data decryption tool
- `*`  →  `Error404`  (src/components/errors/Error404.js)  — 404 fallback

---

## crm-react.raw

All routes are client-side React Router v6, defined in `src/routes/Router.js` and `src/routes/AppRouter.js`. Exact path strings are not fully visible in the skeletonized source; names are inferred from the lazy-import comments.

### Authentication
- `/login`  →  `Login`  (src/pages/Authentication/Login.js)  — User login form
- `/verify-otp`  →  `VerifyOTP`  (src/pages/Authentication/VerifyOTP.js)  — OTP verification
- `/forgot-password`  →  `ForgotPassword`  (src/pages/Authentication/ForgotPassword.js)  — Forgot password
- `/change-password`  →  `ChangePassword`  (src/pages/Authentication/ChangePassword.js)  — Change password
- `/auto-login`  →  `AutoLogin`  (src/pages/Authentication/AutoLogin.jsx)  — Token-based auto login
- `/logout`  →  `Logout`  (src/pages/Authentication/Logout.js)  — Session logout

### Dashboard
- `/dashboard`  →  `Dashboard`  (src/pages/Dashboard/index.js)  — Main KPI dashboard

### Leads
- `/leads/all`  →  `AllLeads`  (src/pages/Leads/AllLeads/index.js)  — All leads list
- `/leads/credit`  →  `CreditLeads`  (src/pages/Leads/CreditLeads/index.js)  — Credit team leads
- `/leads/hot`  →  `HotLeads`  (src/pages/Leads/HotLeads/index.js)  — Hot leads
- `/leads/sanction`  →  `SanctionLeads`  (src/pages/Leads/SanctionLeads/index.js)  — Sanction leads

### Customer Profile
- `/customer-profile`  →  `CustomerProfile`  (src/pages/CustomerProfile/index.js)  — Full customer profile (tabbed)

### Customers
- `/customers`  →  `Customers`  (src/pages/Customers/index.js)  — Customer list
- `/customers/:id/update`  →  `CustomerDetailsUpdate`  (src/pages/Customers/customer-details-update/CustomerDetailsUpdate.js)  — Update customer details

### Collection
- `/collection/pending`  →  `PendingCollection`  (src/pages/Collection/PendingCollection/index.js)  — Pending collections
- `/collection/closed`  →  `Closed`  (src/pages/Collection/Closed/index.js)  — Closed collections
- `/collection/settled`  →  `Settled`  (src/pages/Collection/Settled/index.js)  — Settled collections
- `/collection/part-paid`  →  `PartPaid`  (src/pages/Collection/PartPaid/index.js)  — Part-paid collections
- `/collection/dnd-customer`  →  `DNDCustomer`  (src/pages/Collection/DNDCustomer/index.js)  — DND customer list
- `/collection/add-not-required`  →  `AddNotRequired`  (src/pages/Collection/AddNotRequired/index.js)  — Add-not-required list
- `/collection/bulk-emandate`  →  `BulkEmandate`  (src/pages/Collection/BulkEmandate/BulkEmandate.js)  — Bulk e-mandate upload
- `/collection/waived-off`  →  `WaivedOff`  (src/pages/Collection/WaivedOff/index.js)  — Waived-off loans
- `/collection/payday-payment-pending`  →  `PaydayPaymentPendingEmi`  (src/pages/Collection/PaydayPaymentPendingEmi/index.jsx)  — Payday pending EMI
- `/collection/refund`  →  `Refund`  (src/pages/Collection/Refund/index.jsx)  — Refund management (tabbed)

### Collection Manager
- `/collection-manager`  →  `CollectionManager`  (src/pages/CollectionManager/collectionManager.js)  — Collection manager wrapper
- `/collection-manager/approval-pending`  →  `ApprovalPending`  (src/pages/CollectionManager/ApprovalPending/index.js)  — Pending approvals
- `/collection-manager/approved`  →  `Approved`  (src/pages/CollectionManager/Approved/index.js)  — Approved entries
- `/collection-manager/rejected`  →  `Rejected`  (src/pages/CollectionManager/Rejected/index.js)  — Rejected entries
- `/collection-manager/online-payments`  →  `OnlinePayments`  (src/pages/CollectionManager/OnlinePayments/index.js)  — Online payments
- `/collection-manager/bulk-upload`  →  `BulkUpload`  (src/pages/CollectionManager/BulkUpload/index.js)  — Bulk upload

### Collection Setting
- `/collection-setting/settlement-report`  →  `SettlementReport`  (src/pages/CollectionSetting/SettlementReport/index.js)  — Settlement report

### Disbursal
- `/disbursal/bank-update`  →  `BankUpdate`  (src/pages/Disbursal/BankUpdate/index.js)  — Bank update queue
- `/disbursal/bank-update-rejected`  →  `BankUpdateRejected`  (src/pages/Disbursal/BankUpdateRejected/index.js)  — Rejected bank updates
- `/disbursal/disbursed`  →  `Disbursed`  (src/pages/Disbursal/Disbursed/index.js)  — Disbursed loans
- `/disbursal/manual`  →  `ManualDisbursal`  (src/pages/Disbursal/ManualDisbursal/index.js)  — Manual disbursal upload

### CRM Management
- `/crm/users`  →  `Users`  (src/pages/CRMManagement/Users/index.js)  — User list
- `/crm/users/add`  →  `UserListAdd`  (src/pages/CRMManagement/UserListAdd/index.js)  — Add user
- `/crm/users/:userID/update`  →  `UserListUpdate`  (src/pages/CRMManagement/UserListUpdate/index.js)  — Update user
- `/crm/users/access`  →  `UserListAccess`  (src/pages/CRMManagement/UserListAccess/index.js)  — Manage report access
- `/crm/logins`  →  `Logins`  (src/pages/CRMManagement/Logins/index.js)  — Login history
- `/crm/ip-whitelisting`  →  `IPWhiteListing`  (src/pages/CRMManagement/IPWhiteListing/index.js)  — IP whitelist
- `/crm/permissions`  →  `PermissionsList`  (src/pages/CRMManagement/PermissionsList/index.js)  — Permissions list
- `/crm/roles`  →  `RolesList`  (src/pages/CRMManagement/RolesList/index.js)  — Roles list
- `/crm/roles/permissions`  →  `HavePermission`  (src/pages/CRMManagement/HavePermission/index.js)  — Role-permission mapping
- `/crm/sourcing-partners`  →  `SourcingPartners`  (src/pages/CRMManagement/SourcingPartners/index.js)  — Sourcing partners
- `/crm/dsa-partners`  →  `DSAPartners`  (src/pages/CRMManagement/DSAPartner/index.jsx)  — DSA partners

### App Function Management
- `/app/auto-disbursal-status`  →  `AutoDisbursalStatus`  (src/pages/AppFunctionManagement/AutoDisbursalStatus/index.js)  — Toggle auto disbursal
- `/app/holiday-list`  →  `Holiday`  (src/pages/AppFunctionManagement/HolidayList/index.js)  — Holiday management
- `/app/repayment-gateway-type`  →  `RepaymentGatewayType`  (src/pages/AppFunctionManagement/RepaymentGatewayType/index.js)  — Gateway type config

### Lead Actions
- `/lead-actions/manual-selfie-verification`  →  `ManualSelfieVerification`  (src/pages/LeadActions/ManualSelfieVerification/index.jsx)  — Selfie verification queue
- `/lead-actions/manual-selfie-confirmation`  →  `ManualSelfieConfirmation`  (src/pages/LeadActions/ManualSelfieConfirmation/index.jsx)  — Selfie confirmation
- `/lead-actions/name-mismatch`  →  `NameMismatchManager`  (src/pages/LeadActions/NameMismatchManager/index.js)  — Name mismatch resolution
- `/lead-actions/payment-mode`  →  `PaymentModeManager`  (src/pages/LeadActions/PaymentModeManager/index.js)  — Payment mode management
- `/lead-actions/repayment-date`  →  `RepaymentDateManager`  (src/pages/LeadActions/RepaymentDateManager/index.js)  — Repayment date changes

### Reports
- `/reports`  →  `Report`  (src/pages/Reports/report.js)  — Reports landing
- `/reports/quick`  →  `QuickReportsWrapper`  (src/pages/Reports/quickReportsWrapper.js)  — Quick report selector
- `/reports/quick-download`  →  `QuickReportDownloadRequest`  (src/pages/Reports/quickReportDownloadRequest.jsx)  — Download request queue
- `/reports/all-leads`  →  `AllLeadReports`  (src/pages/Reports/allLeadReports.js)  — All-leads report
- `/reports/date-wise-collection`  →  `DateWiseCollectionReport`  (src/pages/Reports/dateWiseCollectionReport.js)  — Date-wise collection
- `/reports/date-wise-lead`  →  `DateWiseLeadReport`  (src/pages/Reports/dateWiseLeadReport.js)  — Date-wise lead
- `/reports/disbursed`  →  `DisbursedReport`  (src/pages/Reports/disbursedReport.js)  — Disbursed report
- `/reports/disbursed-data`  →  `DisbursedDataReport`  (src/pages/Reports/disbursedDataReport.js)  — Disbursed data
- `/reports/disbursal-dashboard`  →  `DisbursalReportDashboard`  (src/pages/Reports/disbursalReportDashboard.js)  — Disbursal dashboard
- `/reports/collection-data`  →  `CollectionDataReport`  (src/pages/Reports/collectionDataReport.js)  — Collection data
- `/reports/collection-emi`  →  `CollectionEmiDataReport`  (src/pages/Reports/collectionEmiDataReport.js)  — Collection EMI data
- `/reports/collection-payment-mode`  →  `CollectionPaymentMode`  (src/pages/Reports/collectionPaymentMode.js)  — Payment mode report
- `/reports/payday-pending`  →  `PayDayPendingReport`  (src/pages/Reports/payDayPendingReport.js)  — Payday pending
- `/reports/customer-feedback`  →  `CustomerFeedback`  (src/pages/Reports/customerFeedback.js)  — Customer feedback
- `/reports/landing-partner-leads`  →  `LandingPartnerLeads`  (src/pages/Reports/landingPartnerLeads.js)  — Landing partner leads
- `/reports/app-issue-list`  →  `AppIssueListReport`  (src/pages/Reports/appIssueListReport.js)  — App issue list
- `/reports/refund`  →  `RefundReport`  (src/pages/Reports/refundReport.js)  — Refund report
- `/reports/credit-hod`  →  `CreditHODReport`  (src/pages/Reports/CreditHODReport.jsx)  — Credit HOD report
- `/reports/credit-modification`  →  `CreditModificationReport`  (src/pages/Reports/CreditModificationReport.jsx)  — Credit modification
- `/reports/event-funnel`  →  `EventFunnelReport`  (src/pages/Reports/EventFunnelReport.js)  — Event funnel
- `/reports/failed-loan-onboarding`  →  `FailedLoanOnboardingReport`  (src/pages/Reports/FailedLoanOnboardingReport.js)  — Failed onboarding

### Logs
- `/logs/api`  →  `APILogs`  (src/pages/Logs/APILogs/index.js)  — API call logs
- `/logs/app-installations`  →  `AppInstallations`  (src/pages/Logs/AppInstallations/index.js)  — App install logs
- `/logs/chat`  →  `ChatLogs`  (src/pages/Logs/ChatLogs/index.js)  — Chat logs
- `/logs/dialer`  →  `DialerLogs`  (src/pages/Logs/DialerLogs/index.js)  — Dialer logs
- `/logs/kaleyra`  →  `KaleyraLogs`  (src/pages/Logs/KaleyraLogs/index.js)  — Kaleyra logs
- `/logs/razorpay`  →  `RazorpayLogs`  (src/pages/Logs/RazorpayLogs/index.js)  — Razorpay logs
- `/logs/sendinblue`  →  `SendInBlueLogs`  (src/pages/Logs/SendInBlueLogs/index.js)  — SendInBlue logs
- `/logs/whatsapp`  →  `WhatsappLogs`  (src/pages/Logs/WhatsappLogs/index.js)  — WhatsApp logs

### Blacklisted
- `/blacklisted/customers`  →  `BlacklistCustomers`  (src/pages/Blacklisted/BlacklistCustomers/index.js)  — Blacklisted customers
- `/blacklisted/pancard`  →  `BlacklistPancard`  (src/pages/Blacklisted/BlacklistPancard/index.js)  — Blacklisted PANs

### Miscellaneous
- `/cibil`  →  `CibilData`  (src/pages/Cibil/CibilData/index.js)  — CIBIL data
- `/callback-request`  →  `CallbackRequest`  (src/pages/CallbackRequest/index.js)  — Callback requests
- `/feedback`  →  `Feedback`  (src/pages/Feedback/index.jsx)  — Customer feedback list
- `/secure-decryption`  →  `SecureDecryption`  (src/pages/SecureDecryption/index.jsx)  — Data decryption tool
- `*`  →  `Error404`  (src/components/errors/Error404.js)  — 404 fallback

---

## devOpsStack

This repository is infrastructure/DevOps tooling only. No HTTP routes, RPC endpoints, or message handlers are defined in this repo. Application-level routing is declared as Kubernetes Ingress rules pointing to external services.

### Kubernetes Ingress hostnames exposed per chart (nginx ingressClassName unless noted)

**k8s/ (ramfincorp)**
- `HTTPS /*  ->  rf-backend-svc:80`  (k8s/rf-backend/templates/ingress.yaml) — ALB, ramfincorp main backend
- `HTTPS /*  ->  crm-backend-svc:80`  (k8s/crm-backend/templates/ingress.yaml) — ALB, CRM backend
- `HTTPS /*  ->  loan-backend-svc:80`  (k8s/loan-backend/templates/ingress.yaml) — ALB, loan onboarding
- `HTTPS /*  ->  loans-backend-svc:80`  (k8s/loans-backend/templates/ingress.yaml) — ALB, Hyperverge loan onboarding
- `host: dedup.ramfincorp.com /  ->  dedup-svc:80`  (k8s/dedup/templates/ingress.yaml) — nginx, dedup service
- `host: dsa-backend.ramfincorp.com /(.*)  ->  dsa-backend-svc:80`  (k8s/dsa-backend/templates/ingress.yaml) — nginx, DSA backend
- `host: crm-report.ramfincorp.com /(.*)  ->  crm-report-svc:80`  (k8s/crm-report/templates/ingress.yaml) — nginx, CRM reports
- `host: notification.ramfincorp.com /(.*)  ->  notification-svc:80`  (k8s/notification/templates/ingress.yaml) — nginx, notification service
- `host: api-ramfinbackend.ramfincorp.com /(.*)  ->  rf-backend-hyperverge-svc:80`  (k8s/rf-backend-hyperverge/templates/ingress.yaml) — nginx, Hyperverge backend
- `host: userservice.ramfincorp.com /(.*)  ->  userservice-backend-svc:80`  (k8s/userservice-backend/templates/ingress.yaml) — nginx, user service
- `host: grafana.ramfincorp.com /  ->  loki-grafana:80`  (k8s/common-resources/grafana-ingress.yaml) — nginx, Grafana

**kamakshimoney-k8s/ (kamakshimoney)**
- `HTTPS /*  ->  crm-backend-svc:80`  (kamakshimoney-k8s/crm-backend/templates/ingress.yaml) — ALB, KM CRM backend
- `host: api-node.kamakshimoney.com /(.*)  ->  km-backend-svc:80`  (kamakshimoney-k8s/km-backend/templates/ingress.yaml) — nginx, KM main backend
- `host: loan-api.kamakshimoney.com /(.*)  ->  loan-backend-svc:80`  (kamakshimoney-k8s/loan-backend/templates/ingress.yaml) — nginx, KM loan API
- `host: loans-api.kamakshimoney.com /(.*)  ->  loans-backend-svc:80`  (kamakshimoney-k8s/loans-backend/templates/ingress.yaml) — nginx, KM Hyperverge loans
- `host: crm-report.kamakshimoney.com /(.*)  ->  crm-report-svc:80`  (kamakshimoney-k8s/crm-report/templates/ingress.yaml) — nginx, KM CRM reports
- `host: userservice.kamakshimoney.com /(.*)  ->  userservice-backend-svc:80`  (kamakshimoney-k8s/userservice-backend/templates/ingress.yaml) — nginx, KM user service

**eks-cdk-infra (Envoy Gateway / pre-prod)**
- `host: nginx-test.ramfincorp.com  ->  test-nginx-svc:80`  (eks-cdk-infra/ramfincorp/test-app.yaml) — Envoy Gateway HTTPRoute, test nginx
- `host: abc.preprod.ramfincorp.com  ->  your-abc-kubernetes-service-name:8080`  (eks-cdk-infra/ramfincorp/sample-route.yaml) — Envoy Gateway HTTPRoute, sample/template route

### Scheduled jobs
- `CRON 0 * * * *  ->  cleanup PR namespaces`  (.github/workflows/cleanup-pr-namespaces.yaml) — deletes k8s namespaces matching `*-pr-*` older than 4 hours

---

## devOpsStack.raw

This repository is infrastructure/DevOps tooling only. No HTTP routes, RPC endpoints, or message handlers are defined in this repo. Application-level routing is declared as Kubernetes Ingress rules pointing to external services.

### Kubernetes Ingress hostnames exposed per chart (nginx ingressClassName unless noted)

**k8s/ (ramfincorp)**
- `HTTPS /*  ->  rf-backend-svc:80`  (k8s/rf-backend/templates/ingress.yaml) — ALB, ramfincorp main backend
- `HTTPS /*  ->  crm-backend-svc:80`  (k8s/crm-backend/templates/ingress.yaml) — ALB, CRM backend
- `HTTPS /*  ->  loan-backend-svc:80`  (k8s/loan-backend/templates/ingress.yaml) — ALB, loan onboarding
- `HTTPS /*  ->  loans-backend-svc:80`  (k8s/loans-backend/templates/ingress.yaml) — ALB, Hyperverge loan onboarding
- `host: dedup.ramfincorp.com /  ->  dedup-svc:80`  (k8s/dedup/templates/ingress.yaml) — nginx, dedup service
- `host: dsa-backend.ramfincorp.com /(.*)  ->  dsa-backend-svc:80`  (k8s/dsa-backend/templates/ingress.yaml) — nginx, DSA backend
- `host: crm-report.ramfincorp.com /(.*)  ->  crm-report-svc:80`  (k8s/crm-report/templates/ingress.yaml) — nginx, CRM reports
- `host: notification.ramfincorp.com /(.*)  ->  notification-svc:80`  (k8s/notification/templates/ingress.yaml) — nginx, notification service
- `host: api-ramfinbackend.ramfincorp.com /(.*)  ->  rf-backend-hyperverge-svc:80`  (k8s/rf-backend-hyperverge/templates/ingress.yaml) — nginx, Hyperverge backend
- `host: userservice.ramfincorp.com /(.*)  ->  userservice-backend-svc:80`  (k8s/userservice-backend/templates/ingress.yaml) — nginx, user service
- `host: grafana.ramfincorp.com /  ->  loki-grafana:80`  (k8s/common-resources/grafana-ingress.yaml) — nginx, Grafana

**kamakshimoney-k8s/ (kamakshimoney)**
- `HTTPS /*  ->  crm-backend-svc:80`  (kamakshimoney-k8s/crm-backend/templates/ingress.yaml) — ALB, KM CRM backend
- `host: api-node.kamakshimoney.com /(.*)  ->  km-backend-svc:80`  (kamakshimoney-k8s/km-backend/templates/ingress.yaml) — nginx, KM main backend
- `host: loan-api.kamakshimoney.com /(.*)  ->  loan-backend-svc:80`  (kamakshimoney-k8s/loan-backend/templates/ingress.yaml) — nginx, KM loan API
- `host: loans-api.kamakshimoney.com /(.*)  ->  loans-backend-svc:80`  (kamakshimoney-k8s/loans-backend/templates/ingress.yaml) — nginx, KM Hyperverge loans
- `host: crm-report.kamakshimoney.com /(.*)  ->  crm-report-svc:80`  (kamakshimoney-k8s/crm-report/templates/ingress.yaml) — nginx, KM CRM reports
- `host: userservice.kamakshimoney.com /(.*)  ->  userservice-backend-svc:80`  (kamakshimoney-k8s/userservice-backend/templates/ingress.yaml) — nginx, KM user service

**eks-cdk-infra (Envoy Gateway / pre-prod)**
- `host: nginx-test.ramfincorp.com  ->  test-nginx-svc:80`  (eks-cdk-infra/ramfincorp/test-app.yaml) — Envoy Gateway HTTPRoute, test nginx
- `host: abc.preprod.ramfincorp.com  ->  your-abc-kubernetes-service-name:8080`  (eks-cdk-infra/ramfincorp/sample-route.yaml) — Envoy Gateway HTTPRoute, sample/template route

### Scheduled jobs
- `CRON 0 * * * *  ->  cleanup PR namespaces`  (.github/workflows/cleanup-pr-namespaces.yaml) — deletes k8s namespaces matching `*-pr-*` older than 4 hours

---

## kanakloans-webview

All routes are client-side React Router routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes**
```
GET /                        ->  Login                  (src/pages/Login.jsx)             — mobile number entry + OTP login
GET /auto-login              ->  AutoLogin              (src/pages/AutoLogin.jsx)          — token-based auto login
GET /logout                  ->  Logout                 (src/pages/Logout.jsx)             — clears session and redirects
GET /contact-us              ->  ContactUs              (src/pages/ContactUs.jsx)          — contact information page
GET /*                       ->  NotFound               (src/pages/NotFound.jsx)           — 404 fallback
```

**Protected Routes**
```
GET /stepper                 ->  Stepper                (src/pages/Stepper.jsx)            — loan journey step controller
GET /pan-verify              ->  PANVerify              (src/pages/PANVerify.jsx)          — PAN number + pincode + loan purpose entry
GET /employment-details      ->  EmploymentDetails      (src/pages/EmploymentDetails.jsx)  — employment type, income, salary date
GET /select-tenure           ->  SelectTenure           (src/pages/SelectTenure.jsx)       — loan offer/tenure selection
GET /loan-approval           ->  LoanApproval           (src/pages/LoanApproval.jsx)       — display approved loan offer
GET /your-email              ->  YourEmail              (src/pages/YourEmail.jsx)          — email collection with OTP verify
GET /aadhaar-verification    ->  AadhaarVerification    (src/pages/AadhaarVerification.jsx)— Aadhaar entry + OTP or Digilocker
GET /digilocker-verify       ->  DigilockerVerify       (src/pages/DigilockerVerify.jsx)   — Digilocker callback handler
GET /camera-permission       ->  CameraPermission       (src/pages/CameraPermission.jsx)   — request camera access
GET /selfie-verification     ->  Selfie                 (src/pages/Selfie.jsx)             — webcam selfie capture + liveness
GET /selfie-hyperverge       ->  SelfieHyperVerge       (src/pages/SelfieHyperVerge.jsx)   — HyperVerge selfie SDK flow
GET /selfie-hyperverge-result ->  SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result handler
GET /finbox                  ->  Finbox                 (src/pages/Finbox.jsx)             — Finbox bank statement initiation
GET /finbox-status           ->  FinboxStatus           (src/pages/FinboxStatus.jsx)       — Finbox connection status
GET /finbox-error            ->  FinboxError            (src/pages/FinboxError.jsx)        — Finbox error handler
GET /add-bank-account        ->  AddBankAccount         (src/pages/AddBankAccount.jsx)     — manual bank account entry
GET /confirm-bank-account    ->  ConfirmBankAccount     (src/pages/ConfirmBankAccount.jsx) — confirm selected bank account
GET /penny-drop              ->  PennyDrop              (src/pages/PennyDrop.jsx)          — penny drop bank verification
GET /emandate                ->  Emandate               (src/pages/Emandate.jsx)           — e-mandate setup via Razorpay
GET /kfs                     ->  KFS                    (src/pages/KFS.jsx)                — Key Fact Statement acceptance
GET /process-to-bank         ->  ProcessToBank          (src/pages/ProcessToBank.jsx)      — processing/transition screen
GET /disbursed               ->  Disbursed              (src/pages/Disbursed.jsx)          — loan disbursed confirmation
GET /loan-rejected           ->  LoanRejected           (src/pages/LoanRejected.jsx)       — loan rejection screen
```

---

## kanakloans-webview.raw

All routes are client-side React Router routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes**
```
GET /                        ->  Login                  (src/pages/Login.jsx)             — mobile number entry + OTP login
GET /auto-login              ->  AutoLogin              (src/pages/AutoLogin.jsx)          — token-based auto login
GET /logout                  ->  Logout                 (src/pages/Logout.jsx)             — clears session and redirects
GET /contact-us              ->  ContactUs              (src/pages/ContactUs.jsx)          — contact information page
GET /*                       ->  NotFound               (src/pages/NotFound.jsx)           — 404 fallback
```

**Protected Routes**
```
GET /stepper                 ->  Stepper                (src/pages/Stepper.jsx)            — loan journey step controller
GET /pan-verify              ->  PANVerify              (src/pages/PANVerify.jsx)          — PAN number + pincode + loan purpose entry
GET /employment-details      ->  EmploymentDetails      (src/pages/EmploymentDetails.jsx)  — employment type, income, salary date
GET /select-tenure           ->  SelectTenure           (src/pages/SelectTenure.jsx)       — loan offer/tenure selection
GET /loan-approval           ->  LoanApproval           (src/pages/LoanApproval.jsx)       — display approved loan offer
GET /your-email              ->  YourEmail              (src/pages/YourEmail.jsx)          — email collection with OTP verify
GET /aadhaar-verification    ->  AadhaarVerification    (src/pages/AadhaarVerification.jsx)— Aadhaar entry + OTP or Digilocker
GET /digilocker-verify       ->  DigilockerVerify       (src/pages/DigilockerVerify.jsx)   — Digilocker callback handler
GET /camera-permission       ->  CameraPermission       (src/pages/CameraPermission.jsx)   — request camera access
GET /selfie-verification     ->  Selfie                 (src/pages/Selfie.jsx)             — webcam selfie capture + liveness
GET /selfie-hyperverge       ->  SelfieHyperVerge       (src/pages/SelfieHyperVerge.jsx)   — HyperVerge selfie SDK flow
GET /selfie-hyperverge-result ->  SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result handler
GET /finbox                  ->  Finbox                 (src/pages/Finbox.jsx)             — Finbox bank statement initiation
GET /finbox-status           ->  FinboxStatus           (src/pages/FinboxStatus.jsx)       — Finbox connection status
GET /finbox-error            ->  FinboxError            (src/pages/FinboxError.jsx)        — Finbox error handler
GET /add-bank-account        ->  AddBankAccount         (src/pages/AddBankAccount.jsx)     — manual bank account entry
GET /confirm-bank-account    ->  ConfirmBankAccount     (src/pages/ConfirmBankAccount.jsx) — confirm selected bank account
GET /penny-drop              ->  PennyDrop              (src/pages/PennyDrop.jsx)          — penny drop bank verification
GET /emandate                ->  Emandate               (src/pages/Emandate.jsx)           — e-mandate setup via Razorpay
GET /kfs                     ->  KFS                    (src/pages/KFS.jsx)                — Key Fact Statement acceptance
GET /process-to-bank         ->  ProcessToBank          (src/pages/ProcessToBank.jsx)      — processing/transition screen
GET /disbursed               ->  Disbursed              (src/pages/Disbursed.jsx)          — loan disbursed confirmation
GET /loan-rejected           ->  LoanRejected           (src/pages/LoanRejected.jsx)       — loan rejection screen
```

---

## node-crm

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

## node-crm.raw

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

## node_crm

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

## node_crm.raw

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

## onboarding-service-frontend

All routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes**
```
GET /                    ->  Login               (src/pages/Login.jsx)          — Mobile OTP login
GET /auto-login          ->  AutoLogin           (src/pages/AutoLogin.jsx)       — Token-based auto login
GET /logout              ->  Logout              (src/pages/Logout.jsx)          — Clear session and redirect
GET /*                   ->  NotFound            (src/pages/NotFound.jsx)        — 404 fallback
```

**Protected Routes (require auth)**
```
GET /stepper             ->  Stepper             (src/pages/Stepper.jsx)                 — Step checker/router
GET /pan-verify          ->  PANVerify           (src/pages/PANVerify.jsx)               — PAN number input and confirmation
GET /pan-verify-rejected ->  PANVerifyRejected   (src/pages/PANVerifyRejected.jsx)       — Age ineligibility screen
GET /employment-details  ->  EmploymentDetails   (src/pages/EmploymentDetails.jsx)       — Employment/income form
GET /finbox              ->  Finbox              (src/pages/Finbox.jsx)                  — Finbox bank statement widget
GET /finbox-error        ->  FinboxError         (src/pages/FinboxError.jsx)             — Finbox failure screen
GET /finbox-status       ->  FinboxStatus        (src/pages/FinboxStatus.jsx)            — Finbox status check
GET /select-tenure       ->  SelectTenure        (src/pages/SelectTenure.jsx)            — Choose loan offer/tenure
GET /loan-approval       ->  LoanApproval        (src/pages/LoanApproval.jsx)            — Loan approval details + bank confirm
GET /loan-rejected       ->  LoanRejected        (src/pages/LoanRejected.jsx)            — Application rejected screen
GET /your-email          ->  YourEmail           (src/pages/YourEmail.jsx)               — Email input + OTP verify
GET /aadhaar-verification ->  AadhaarVerification (src/pages/AadhaarVerification.jsx)   — Aadhaar OTP or Digilocker KYC
GET /digilocker-verify   ->  DigilockerVerify    (src/pages/DigilockerVerify.jsx)        — Digilocker webhook result
GET /camera-permission   ->  CameraPermission    (src/pages/CameraPermission.jsx)        — Camera access guide (commented out in routes)
GET /selfie-verification ->  Selfie              (src/pages/Selfie.jsx)                  — Selfie capture (commented out in routes)
GET /selfie-hyperverge   ->  SelfieHyperVerge    (src/pages/SelfieHyperVerge.jsx)        — HyperVerge selfie flow
GET /selfie-hyperverge-result -> SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result
GET /add-bank-account    ->  AddBankAccount      (src/pages/AddBankAccount.jsx)          — Bank account form
GET /penny-drop          ->  PennyDrop           (src/pages/PennyDrop.jsx)               — Penny drop verification
GET /emandate            ->  Emandate            (src/pages/Emandate.jsx)                — E-mandate setup
GET /kfs                 ->  KFS                 (src/pages/KFS.jsx)                     — Key Fact Statement acceptance
GET /disbursed           ->  Disbursed           (src/pages/Disbursed.jsx)               — Loan disbursed success screen
```

---

## onboarding-service-frontend.raw

All routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes**
```
GET /                    ->  Login               (src/pages/Login.jsx)          — Mobile OTP login
GET /auto-login          ->  AutoLogin           (src/pages/AutoLogin.jsx)       — Token-based auto login
GET /logout              ->  Logout              (src/pages/Logout.jsx)          — Clear session and redirect
GET /*                   ->  NotFound            (src/pages/NotFound.jsx)        — 404 fallback
```

**Protected Routes (require auth)**
```
GET /stepper             ->  Stepper             (src/pages/Stepper.jsx)                 — Step checker/router
GET /pan-verify          ->  PANVerify           (src/pages/PANVerify.jsx)               — PAN number input and confirmation
GET /pan-verify-rejected ->  PANVerifyRejected   (src/pages/PANVerifyRejected.jsx)       — Age ineligibility screen
GET /employment-details  ->  EmploymentDetails   (src/pages/EmploymentDetails.jsx)       — Employment/income form
GET /finbox              ->  Finbox              (src/pages/Finbox.jsx)                  — Finbox bank statement widget
GET /finbox-error        ->  FinboxError         (src/pages/FinboxError.jsx)             — Finbox failure screen
GET /finbox-status       ->  FinboxStatus        (src/pages/FinboxStatus.jsx)            — Finbox status check
GET /select-tenure       ->  SelectTenure        (src/pages/SelectTenure.jsx)            — Choose loan offer/tenure
GET /loan-approval       ->  LoanApproval        (src/pages/LoanApproval.jsx)            — Loan approval details + bank confirm
GET /loan-rejected       ->  LoanRejected        (src/pages/LoanRejected.jsx)            — Application rejected screen
GET /your-email          ->  YourEmail           (src/pages/YourEmail.jsx)               — Email input + OTP verify
GET /aadhaar-verification ->  AadhaarVerification (src/pages/AadhaarVerification.jsx)   — Aadhaar OTP or Digilocker KYC
GET /digilocker-verify   ->  DigilockerVerify    (src/pages/DigilockerVerify.jsx)        — Digilocker webhook result
GET /camera-permission   ->  CameraPermission    (src/pages/CameraPermission.jsx)        — Camera access guide (commented out in routes)
GET /selfie-verification ->  Selfie              (src/pages/Selfie.jsx)                  — Selfie capture (commented out in routes)
GET /selfie-hyperverge   ->  SelfieHyperVerge    (src/pages/SelfieHyperVerge.jsx)        — HyperVerge selfie flow
GET /selfie-hyperverge-result -> SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result
GET /add-bank-account    ->  AddBankAccount      (src/pages/AddBankAccount.jsx)          — Bank account form
GET /penny-drop          ->  PennyDrop           (src/pages/PennyDrop.jsx)               — Penny drop verification
GET /emandate            ->  Emandate            (src/pages/Emandate.jsx)                — E-mandate setup
GET /kfs                 ->  KFS                 (src/pages/KFS.jsx)                     — Key Fact Statement acceptance
GET /disbursed           ->  Disbursed           (src/pages/Disbursed.jsx)               — Loan disbursed success screen
```

---

## onboarding-service

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

## onboarding_service_frontend

All routes are client-side React Router routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes**
```
GET /                    ->  Login              (src/pages/Login.jsx)           — Mobile number entry + OTP login
GET /auto-login          ->  AutoLogin          (src/pages/AutoLogin.jsx)       — Token-based auto login
GET /logout              ->  Logout             (src/pages/Logout.jsx)          — Clear session and redirect
GET /not-found           ->  NotFound           (src/pages/NotFound.jsx)        — 404 page
GET /*                   ->  NotFound           (src/pages/NotFound.jsx)        — Catch-all fallback
```

**Protected Routes** (wrapped in `ProtectedRoutes`)
```
GET /stepper             ->  Stepper            (src/pages/Stepper.jsx)              — Step checker / router
GET /pan-verify          ->  PANVerify          (src/pages/PANVerify.jsx)            — PAN entry + confirmation
GET /pan-verify-rejected ->  PANVerifyRejected  (src/pages/PANVerifyRejected.jsx)    — Age-based PAN rejection
GET /employment-details  ->  EmploymentDetails  (src/pages/EmploymentDetails.jsx)    — Employment & income entry
GET /finbox              ->  Finbox             (src/pages/Finbox.jsx)               — Finbox bank statement AA
GET /finbox-error        ->  FinboxError        (src/pages/FinboxError.jsx)          — Finbox failure screen
GET /finbox-status       ->  FinboxStatus       (src/pages/FinboxStatus.jsx)         — Finbox AA status check
GET /select-tenure       ->  SelectTenure       (src/pages/SelectTenure.jsx)         — Loan offer selection
GET /loan-approval       ->  LoanApproval       (src/pages/LoanApproval.jsx)         — Loan approval details
GET /loan-rejected       ->  LoanRejected       (src/pages/LoanRejected.jsx)         — Loan rejection screen
GET /your-email          ->  YourEmail          (src/pages/YourEmail.jsx)            — Email entry + OTP verify
GET /aadhaar-verification ->  AadhaarVerification (src/pages/AadhaarVerification.jsx) — Aadhaar OTP / Digilocker KYC
GET /digilocker-verify   ->  DigilockerVerify   (src/pages/DigilockerVerify.jsx)     — Digilocker webhook result
GET /selfie-verification ->  SelfieHyperVerge   (src/pages/SelfieHyperVerge.jsx)     — HyperVerge selfie (active)
GET /selfie-result       ->  SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result
GET /add-bank-account    ->  AddBankAccount     (src/pages/AddBankAccount.jsx)       — Bank account entry
GET /emandate            ->  Emandate           (src/pages/Emandate.jsx)             — E-mandate setup
GET /penny-drop          ->  PennyDrop          (src/pages/PennyDrop.jsx)            — Penny drop verification
GET /kfs                 ->  KFS                (src/pages/KFS.jsx)                  — Key Fact Statement acceptance
GET /disbursed           ->  Disbursed          (src/pages/Disbursed.jsx)            — Loan disbursed success screen
```

Note: `camera-permission` and `selfie-verification` (old Selfie component) routes are commented out in AppRoutes.jsx.

---

## onboarding_service_frontend.raw

All routes are client-side React Router routes defined in `src/routes/AppRoutes.jsx`.

**Public Routes**
```
GET /                    ->  Login              (src/pages/Login.jsx)           — Mobile number entry + OTP login
GET /auto-login          ->  AutoLogin          (src/pages/AutoLogin.jsx)       — Token-based auto login
GET /logout              ->  Logout             (src/pages/Logout.jsx)          — Clear session and redirect
GET /not-found           ->  NotFound           (src/pages/NotFound.jsx)        — 404 page
GET /*                   ->  NotFound           (src/pages/NotFound.jsx)        — Catch-all fallback
```

**Protected Routes** (wrapped in `ProtectedRoutes`)
```
GET /stepper             ->  Stepper            (src/pages/Stepper.jsx)              — Step checker / router
GET /pan-verify          ->  PANVerify          (src/pages/PANVerify.jsx)            — PAN entry + confirmation
GET /pan-verify-rejected ->  PANVerifyRejected  (src/pages/PANVerifyRejected.jsx)    — Age-based PAN rejection
GET /employment-details  ->  EmploymentDetails  (src/pages/EmploymentDetails.jsx)    — Employment & income entry
GET /finbox              ->  Finbox             (src/pages/Finbox.jsx)               — Finbox bank statement AA
GET /finbox-error        ->  FinboxError        (src/pages/FinboxError.jsx)          — Finbox failure screen
GET /finbox-status       ->  FinboxStatus       (src/pages/FinboxStatus.jsx)         — Finbox AA status check
GET /select-tenure       ->  SelectTenure       (src/pages/SelectTenure.jsx)         — Loan offer selection
GET /loan-approval       ->  LoanApproval       (src/pages/LoanApproval.jsx)         — Loan approval details
GET /loan-rejected       ->  LoanRejected       (src/pages/LoanRejected.jsx)         — Loan rejection screen
GET /your-email          ->  YourEmail          (src/pages/YourEmail.jsx)            — Email entry + OTP verify
GET /aadhaar-verification ->  AadhaarVerification (src/pages/AadhaarVerification.jsx) — Aadhaar OTP / Digilocker KYC
GET /digilocker-verify   ->  DigilockerVerify   (src/pages/DigilockerVerify.jsx)     — Digilocker webhook result
GET /selfie-verification ->  SelfieHyperVerge   (src/pages/SelfieHyperVerge.jsx)     — HyperVerge selfie (active)
GET /selfie-result       ->  SelfieHyperVergeResult (src/pages/SelfieHyperVergeResult.jsx) — HyperVerge result
GET /add-bank-account    ->  AddBankAccount     (src/pages/AddBankAccount.jsx)       — Bank account entry
GET /emandate            ->  Emandate           (src/pages/Emandate.jsx)             — E-mandate setup
GET /penny-drop          ->  PennyDrop          (src/pages/PennyDrop.jsx)            — Penny drop verification
GET /kfs                 ->  KFS                (src/pages/KFS.jsx)                  — Key Fact Statement acceptance
GET /disbursed           ->  Disbursed          (src/pages/Disbursed.jsx)            — Loan disbursed success screen
```

Note: `camera-permission` and `selfie-verification` (old Selfie component) routes are commented out in AppRoutes.jsx.

---

## ramfin-report

### Index
`GET  /  ->  IndexController  (src/routes/index.route.ts)  — health check / index`

### Report (`src/routes/report.route.ts`)
`GET  /report/customer-feedback  ->  ReportController.getCustomerFeedbackReport  (src/routes/report.route.ts)  — paginated customer feedback report`
`GET  /report/disbursal-data  ->  ReportController.getDisbursalDataReport  (src/routes/report.route.ts)  — disbursal data report`
`GET  /report/disbursal-data/download  ->  ReportController.downloadDisbursalDataReport  (src/routes/report.route.ts)  — Excel download for disbursal data report`
`GET  /report/collection-data  ->  ReportController.getCollectionDataReport  (src/routes/report.route.ts)  — collection data report`
`GET  /report/collection-data/download  ->  ReportController.downloadCollectionDataReport  (src/routes/report.route.ts)  — Excel download for collection data report`
`GET  /report/date-wise-pending-payment  ->  ReportController.getDateWisePendingPaymentReport  (src/routes/report.route.ts)  — date-wise pending payment report`
`GET  /report/date-wise-lead  ->  ReportController.getDateWiseLeadReport  (src/routes/report.route.ts)  — date-wise lead report`
`GET  /report/date-wise-lead/download  ->  ReportController.downloadDateWiseLeadReport  (src/routes/report.route.ts)  — Excel download for date-wise lead report`
`GET  /report/date-wise-collection  ->  ReportController.getDateWiseCollectionReport  (src/routes/report.route.ts)  — date-wise collection report`
`GET  /report/date-wise-collection/download  ->  ReportController.downloadDateWiseCollectionReport  (src/routes/report.route.ts)  — Excel download for date-wise collection report`
`GET  /report/app-issue  ->  ReportController.getAppIssueReport  (src/routes/report.route.ts)  — app issue report`
`GET  /report/refund  ->  ReportController.getRefundReport  (src/routes/report.route.ts)  — refund report`
`GET  /report/utm-sources  ->  ReportController.getAllUtmSources  (src/routes/report.route.ts)  — all UTM sources`
`GET  /report/all-leads  ->  ReportController.getAllLeadsReport  (src/routes/report.route.ts)  — all leads report`
`GET  /report/refund/download  ->  ReportController.downloadRefundReport  (src/routes/report.route.ts)  — Excel download for refund report`
`GET  /report/landing-partner-leads  ->  ReportController.getLandingPartnerLeadsReport  (src/routes/report.route.ts)  — landing partner leads report`
`GET  /report/collection-emi  ->  ReportController.getCollectionEmiReport  (src/routes/report.route.ts)  — collection EMI report`
`GET  /report/settlement  ->  ReportController.getSettlementReport  (src/routes/report.route.ts)  — settlement report`
`GET  /report/collection-mode  ->  ReportController.getCollectionModeReport  (src/routes/report.route.ts)  — collection payment mode report`
`GET  /report/disbursal  ->  ReportController.getDisbursalReport  (src/routes/report.route.ts)  — disbursal summary report`
`GET  /report/event-funnel  ->  EventFunnelController  (src/routes/report.route.ts)  — event funnel analytics report`

### Report Summary (`src/routes/reportSummary.route.ts`)
`GET  /report-summary  ->  reportSummary (ReportController)  (src/routes/reportSummary.route.ts)  — report summary`

### Quick Report (`src/routes/quickReport.route.ts`)
`GET   /quick-report/menu  ->  QuickReportController.getMenu  (src/routes/quickReport.route.ts)  — get available report menu for user`
`GET   /quick-report  ->  QuickReportController.getReports  (src/routes/quickReport.route.ts)  — paginated quick report data`
`POST  /quick-report/download  ->  QuickReportController.download  (src/routes/quickReport.route.ts)  — enqueue async report download (SQS)`
`GET   /quick-report/download-list  ->  QuickReportController.getDownloadList  (src/routes/quickReport.route.ts)  — list download log entries for user`
`GET   /quick-report/download-url/:logId  ->  QuickReportController.generateDownloadUrl  (src/routes/quickReport.route.ts)  — generate presigned S3 URL for a completed report`

### Lead (`src/routes/lead.route.ts`)
`GET   /lead/loan-modification  ->  LEADController.loanModificationList  (src/routes/lead.route.ts)  — loan modification list`
`GET   /lead/loan-modification-report  ->  LEADController.loanModificationReport  (src/routes/lead.route.ts)  — loan modification report`

---

## ramfin-report.raw

### Index
`GET  /  ->  IndexController  (src/routes/index.route.ts)  — health check / index`

### Report (`src/routes/report.route.ts`)
`GET  /report/customer-feedback  ->  ReportController.getCustomerFeedbackReport  (src/routes/report.route.ts)  — paginated customer feedback report`
`GET  /report/disbursal-data  ->  ReportController.getDisbursalDataReport  (src/routes/report.route.ts)  — disbursal data report`
`GET  /report/disbursal-data/download  ->  ReportController.downloadDisbursalDataReport  (src/routes/report.route.ts)  — Excel download for disbursal data report`
`GET  /report/collection-data  ->  ReportController.getCollectionDataReport  (src/routes/report.route.ts)  — collection data report`
`GET  /report/collection-data/download  ->  ReportController.downloadCollectionDataReport  (src/routes/report.route.ts)  — Excel download for collection data report`
`GET  /report/date-wise-pending-payment  ->  ReportController.getDateWisePendingPaymentReport  (src/routes/report.route.ts)  — date-wise pending payment report`
`GET  /report/date-wise-lead  ->  ReportController.getDateWiseLeadReport  (src/routes/report.route.ts)  — date-wise lead report`
`GET  /report/date-wise-lead/download  ->  ReportController.downloadDateWiseLeadReport  (src/routes/report.route.ts)  — Excel download for date-wise lead report`
`GET  /report/date-wise-collection  ->  ReportController.getDateWiseCollectionReport  (src/routes/report.route.ts)  — date-wise collection report`
`GET  /report/date-wise-collection/download  ->  ReportController.downloadDateWiseCollectionReport  (src/routes/report.route.ts)  — Excel download for date-wise collection report`
`GET  /report/app-issue  ->  ReportController.getAppIssueReport  (src/routes/report.route.ts)  — app issue report`
`GET  /report/refund  ->  ReportController.getRefundReport  (src/routes/report.route.ts)  — refund report`
`GET  /report/utm-sources  ->  ReportController.getAllUtmSources  (src/routes/report.route.ts)  — all UTM sources`
`GET  /report/all-leads  ->  ReportController.getAllLeadsReport  (src/routes/report.route.ts)  — all leads report`
`GET  /report/refund/download  ->  ReportController.downloadRefundReport  (src/routes/report.route.ts)  — Excel download for refund report`
`GET  /report/landing-partner-leads  ->  ReportController.getLandingPartnerLeadsReport  (src/routes/report.route.ts)  — landing partner leads report`
`GET  /report/collection-emi  ->  ReportController.getCollectionEmiReport  (src/routes/report.route.ts)  — collection EMI report`
`GET  /report/settlement  ->  ReportController.getSettlementReport  (src/routes/report.route.ts)  — settlement report`
`GET  /report/collection-mode  ->  ReportController.getCollectionModeReport  (src/routes/report.route.ts)  — collection payment mode report`
`GET  /report/disbursal  ->  ReportController.getDisbursalReport  (src/routes/report.route.ts)  — disbursal summary report`
`GET  /report/event-funnel  ->  EventFunnelController  (src/routes/report.route.ts)  — event funnel analytics report`

### Report Summary (`src/routes/reportSummary.route.ts`)
`GET  /report-summary  ->  reportSummary (ReportController)  (src/routes/reportSummary.route.ts)  — report summary`

### Quick Report (`src/routes/quickReport.route.ts`)
`GET   /quick-report/menu  ->  QuickReportController.getMenu  (src/routes/quickReport.route.ts)  — get available report menu for user`
`GET   /quick-report  ->  QuickReportController.getReports  (src/routes/quickReport.route.ts)  — paginated quick report data`
`POST  /quick-report/download  ->  QuickReportController.download  (src/routes/quickReport.route.ts)  — enqueue async report download (SQS)`
`GET   /quick-report/download-list  ->  QuickReportController.getDownloadList  (src/routes/quickReport.route.ts)  — list download log entries for user`
`GET   /quick-report/download-url/:logId  ->  QuickReportController.generateDownloadUrl  (src/routes/quickReport.route.ts)  — generate presigned S3 URL for a completed report`

### Lead (`src/routes/lead.route.ts`)
`GET   /lead/loan-modification  ->  LEADController.loanModificationList  (src/routes/lead.route.ts)  — loan modification list`
`GET   /lead/loan-modification-report  ->  LEADController.loanModificationReport  (src/routes/lead.route.ts)  — loan modification report`

---

## ramfin_userservice

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

## ramfin_userservice.raw

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

## ramfincorp-backend

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

## ramfincorp-backend.raw

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

## ramfincorp-notification

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

## ramfincorp-notification.raw

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

## stored-procedure-RamFin

No routes exposed. This repository contains only MySQL stored procedures; there is no HTTP server, RPC layer, or message queue consumer.

---

## stored-procedure-RamFin.raw

No routes exposed. This repository contains only MySQL stored procedures; there is no HTTP server, RPC layer, or message queue consumer.

---

