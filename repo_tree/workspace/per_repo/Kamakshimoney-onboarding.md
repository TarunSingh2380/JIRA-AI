## ARCHITECTURE
**Type:** React SPA (Single Page Application) — loan onboarding frontend for Kamakshi Money.

**Entry Points:**
- `index.html` → `src/main.jsx` (bootstraps React, Redux store, Google OAuth provider, CleverTap)
- `src/App.jsx` → `src/routes/AppRoutes.jsx` (root routing)

**Top-level Modules:**
```
src/
├── main.jsx              — App bootstrap, Redux Provider, Google OAuth, CleverTap init
├── App.jsx               — Root component
├── routes/
│   ├── AppRoutes.jsx     — All route definitions (lazy-loaded pages)
│   └── ProtectedRoutes.jsx — Auth guard wrapper
├── pages/                — 28 page-level components (one per onboarding step)
├── components/           — Reusable UI components (forms, shared, feature-specific)
├── redux/
│   ├── store.js          — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js   — UI state (loading, stepper, install prompt)
│       └── userSlice.js  — User/loan journey state
├── services/
│   ├── userService.js    — All API call functions (backend REST calls via axios)
│   └── dashboardService.js — Empty/placeholder
├── utils/
│   ├── apiClient.js      — Axios wrapper (callApi)
│   ├── encryption.js     — AES decryption utility
│   ├── storage.js        — localStorage abstraction
│   ├── helper.js         — Utility functions
│   └── lazyWithRetry.js  — Lazy import with retry
├── events/
│   └── clevertapEvents.js — CleverTap event push functions
├── lib/
│   ├── clevertap.js      — CleverTap SDK init
│   └── razorpay.js       — Razorpay e-mandate integration
└── hooks/                — Custom hooks (stepper, toast, page tracking, back-button)
```

**External Services:**
- **Backend REST API** — via `apiClient.js` (base URL from env vars)
- **CleverTap** — analytics/event tracking (`clevertap-web-sdk`)
- **Google OAuth** — `@react-oauth/google`, `googleAuthAPI`
- **Razorpay** — e-mandate payment flow (`src/lib/razorpay.js`)
- **HyperVerge** — selfie/KYC verification (`SelfieHyperVerge.jsx`)
- **Finbox** — bank statement/banking surrogate (`Finbox.jsx`)
- **Digilocker** — Aadhaar KYC (`DigilockerVerify.jsx`)
- **Google Analytics (GA4)** — `gtag` in `index.html`
- **Meta Pixel** — `fbq` in `index.html`
- **Microsoft Clarity** — script in `index.html`
- **AWS S3 + CloudFront** — production hosting (deploy workflow)

**Core Loan Onboarding Flow (page sequence):**
Login → PANVerify → EmploymentDetails → SelectTenure → LoanApproval → YourEmail → AadhaarVerification → CameraPermission → Selfie/SelfieHyperVerge → AddBankAccount → ConfirmBankAccount → Emandate → PennyDrop → KFS → Disbursed

---

## ROUTES
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

## DATA_MODELS
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
