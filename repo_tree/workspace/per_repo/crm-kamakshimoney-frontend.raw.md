## ARCHITECTURE

**Entry Points**
- `src/index.js` — React app bootstrap, mounts `<App />`
- `src/App.js` — Root component, wraps router and Redux provider
- `src/routes/AppRouter.js` — Top-level router (authentication guard)
- `src/routes/Router.js` — Lazy-loaded route definitions for all pages

**Top-Level Modules**
```
src/
├── pages/          — Feature pages (40+ modules, each with sub-components)
├── components/     — Shared/reusable UI components
├── services/       — API service classes (extend BaseAPI)
├── redux/          — Redux Toolkit store, slices, middleware
├── hooks/          — Custom React hooks
├── hoc/            — Higher-order components (permissions)
├── lib/            — File download helpers, generic helpers
├── utils/          — API fetch wrapper, storage, environment, auto-logout
├── validation/     — Yup validation schemas
├── constants/      — Dropdowns, menus, master data, endpoints
└── scss/           — Global SCSS design tokens and utilities
```

**Service Layer (all extend `BaseAPI`)**
- `AdminAPI`, `AuthAPI`, `AppFunctionManagementAPI`, `CollectionAPI`, `CollectionSettingAPI`
- `CommonAPI`, `CRMManagementAPI`, `CustomerProfileAPI`, `DashboardAPI`
- `Disbursal`, `LeadActions`, `LeadsAPI`, `LogsAPI`, `QuickReportAPI`, `RefundAPI`, `ReportAPI`
- `upload-api.js` — standalone upload functions

**State Management**
- Redux Toolkit + redux-persist (`localStorage`, `user` slice persisted)
- Slices: `userSlice`, `appSlice`, `navbarSlice`, `paginationSlice`, `apiSlice`

**External Services**
- Backend REST API (URL from `src/utils/environment.js`)
- AWS S3 — file uploads and downloads (refund CSV, manual disbursal)
- AWS CloudFront — CDN for built assets (`E3KVVACOIT7Q7W`)
- Razorpay — payment/disbursal updates
- Kaleyra — SMS/call logs
- SendInBlue — email logs
- Whatsapp API — messaging logs

**Core Request Lifecycle**
1. Component mounts → calls service method (e.g., `CollectionAPI.fetchXxx()`)
2. Service `makeRequest()` in `BaseAPI` calls `utils/api.js` (`apiData()`) via Axios
3. Response dispatched to Redux slice or set in local state
4. Pagination updated via `paginationSlice`; errors shown via `react-toastify`

**CI/CD**
- GitHub Actions (`deploy-main.yml`): `npm build` → `aws s3 cp` → CloudFront invalidation on push to `main`

---

## ROUTES

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

## DATA_MODELS

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