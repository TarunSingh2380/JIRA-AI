## ARCHITECTURE

React 19 SPA (Vite build tool) for a loan onboarding journey targeting Ram Fincorp customers.

**Entry Points**
- `index.html` → `src/main.jsx` — mounts React app, wraps in Redux Provider, Google OAuth Provider, PWA service worker registration
- `src/App.jsx` — renders `AppRoutes`

**Top-Level Modules**
```
src/
├── main.jsx              — app bootstrap, Redux Provider, Google OAuth
├── App.jsx               — root component
├── routes/
│   ├── AppRoutes.jsx     — route definitions, InactivityLogout wrapper
│   └── ProtectedRoutes.jsx — auth guard (checks local storage token)
├── pages/                — 27 page-level components (one per loan journey step)
├── components/           — reusable UI (forms, shared layout, step-specific modals)
├── redux/
│   ├── store.js          — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js   — loading state, stepper, PWA install trigger
│       └── userSlice.js  — mobile, requestId, customer, lead, employment, loanOffer, accountId
├── services/
│   └── userService.js    — all API call functions (30+ functions over REST)
├── utils/
│   ├── apiClient.js      — axios wrapper (callApi)
│   ├── encryption.js     — AES decryption of API responses
│   ├── storage.js        — localStorage wrapper + KEYS constants
│   ├── helper.js         — delay, redirect, UTM, geolocation utilities
│   └── validation.js     — Yup schemas
├── events/
│   └── clevertapEvents.js — CleverTap analytics event push functions
├── lib/
│   ├── clevertap.js      — CleverTap SDK init
│   └── razorpay.js       — Razorpay e-mandate integration
└── i18n/                 — i18next, locales: en/hi/ka
```

**External Services**
- `VITE_BASE_URL` (Node onboarding API) — primary backend
- `VITE_PHP_BASE_URL` — legacy PHP backend
- `VITE_USER_SERVICE_BASE_URL` — user microservice
- Lentra API (`serviceurl.in`) — unclear purpose (CKYC/KYC)
- Razorpay — e-mandate payments
- CleverTap — analytics/event tracking
- Google OAuth — email sign-in
- Digilocker — KYC verification
- HyperVerge — selfie/liveness verification
- Finbox — bank account statement (AA flow)
- Google Analytics (gtag G-W55TK1ES3Z), Meta Pixel, Microsoft Clarity

**Core Request Lifecycle**
1. User navigates to a page → `ProtectedRoutes` checks JWT in localStorage
2. Page component calls service function → `callApi` (axios + optional delay) → backend REST API
3. Response dispatched to Redux slices; UI updates via selectors
4. CleverTap events fired at key journey milestones

---

## ROUTES

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

## DATA_MODELS

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