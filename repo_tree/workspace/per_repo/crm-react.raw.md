## ARCHITECTURE

React 18 SPA (Create React App), deployed to AWS S3 + CloudFront.

```
src/
├── index.js                   Entry point — mounts <App /> with Redux Provider
├── App.js                     Root component — wraps AppRouter
├── routes/
│   ├── AppRouter.js           Top-level router (auth guards, layout wrapper)
│   └── Router.js              Lazy-loaded route definitions for all pages
├── layout/
│   └── Layout.js              Sidebar (Navbar) + Header shell
├── pages/                     Feature pages (grouped by domain)
│   ├── Authentication/        Login, Logout, VerifyOTP, ForgotPassword, ChangePassword, AutoLogin
│   ├── Dashboard/
│   ├── Leads/                 AllLeads, CreditLeads, HotLeads, SanctionLeads
│   ├── CustomerProfile/       UserInfo, LoanApplication, Collection, Communication, Documents, HistoricalData, TimeLine, ApiLogs
│   ├── Collection/            PendingCollection, Closed, Settled, PartPaid, DNDCustomer, AddNotRequired, BulkEmandate, WaivedOff, PaydayPaymentPendingEmi, Refund
│   ├── CollectionManager/     ApprovalPending, Approved, Rejected, OnlinePayments, BulkUpload
│   ├── CollectionSetting/     SettlementReport
│   ├── Disbursal/             BankUpdate, BankUpdateRejected, Disbursed, ManualDisbursal
│   ├── CRMManagement/         Users, Logins, Roles, Permissions, IPWhiteListing, SourcingPartners, DSAPartner, UserListAdd/Update/Access, HavePermission
│   ├── Logs/                  APILogs, AppInstallations, ChatLogs, DialerLogs, KaleyraLogs, RazorpayLogs, SendInBlueLogs, WhatsappLogs
│   ├── Reports/               ~20 report pages (quick, date-wise, disbursal, collection, etc.)
│   ├── AppFunctionManagement/ AutoDisbursalStatus, HolidayList, RepaymentGatewayType
│   ├── LeadActions/           ManualSelfieVerification/Confirmation, NameMismatchManager, PaymentModeManager, RepaymentDateManager
│   ├── Blacklisted/           BlacklistCustomers, BlacklistPancard
│   ├── Cibil/, Customers/, Feedback/, SecureDecryption/, CallbackRequest/
├── services/                  API layer — class-based, all extend BaseAPI
│   ├── BaseAPI.js             axios wrapper, error handling, auth token injection
│   ├── AuthAPI, AdminAPI, CustomerProfileAPI, CollectionAPI, CollectionSettingAPI
│   ├── LeadsAPI, LeadActions, DashboardAPI, Disbursal, CRMManagementAPI
│   ├── AppFunctionManagementAPI, LogsAPI, ReportAPI, QuickReportAPI, RefundAPI
│   ├── CommonAPI, LentraAPI, upload-api.js
├── redux/
│   ├── store.js               Redux Toolkit store; redux-persist whitelist: ["user"]
│   └── slices/                userSlice, appSlice, paginationSlice, navbarSlice, apiSlice(s)
├── components/                Shared UI components (Header, Navbar, Loader, Pagination, Filter, etc.)
├── hooks/                     useFetchWithFilter, useResetPagination, useRouteCheck, useWindowSize
├── hoc/                       withDownloadPermission, withViewAccess
├── utils/                     api.js (axios), autoLogout.js, storage.js (token), environment.js
├── constants/                 dropdown.js, master.js, menu.js, report.js, endpoints.js
└── validation/                Yup schemas (Auth, CRMManagement, CustomerProfile, DndAdd, Leads)
```

**External services consumed:**
- Backend REST API (URL from `src/utils/environment.js`)
- AWS S3 (file uploads/downloads, static hosting)
- Razorpay (disbursal/payment status)
- Kaleyra (SMS/call logs)
- SendInBlue (email logs)
- AWS CloudFront (CDN/invalidation on deploy)

**Core lifecycle:** User authenticates → token stored in localStorage via `storage.js` → persisted in Redux `userSlice` → `AppRouter` checks auth → `Layout` renders sidebar + header → page components call service class methods → results stored locally in component state or Redux slices → `paginationSlice` drives paginated tables → `autoLogout` monitors inactivity.

---

## ROUTES

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

## DATA_MODELS

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