## ARCHITECTURE

**Entry Points**
- `index.html` — single HTML shell, mounts React app at `#root`
- `src/main.jsx` — bootstraps React, wraps app with Redux Provider, Google OAuth Provider, initializes CleverTap

**Top-Level Module Tree**
```
src/
├── App.jsx                  — root component, renders AppRoutes
├── routes/
│   ├── AppRoutes.jsx        — React Router route definitions, InactivityLogout wrapper
│   └── ProtectedRoutes.jsx  — auth guard for protected pages
├── pages/                   — one component per route/screen (30+ pages)
├── components/              — reusable UI components (forms, shared, feature drawers)
├── redux/
│   ├── store.js             — Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js      — loading, stepper, install state
│       └── userSlice.js     — mobile, customer, lead, employment, loan offer state
├── services/
│   └── userService.js       — all API call functions (axios via apiClient)
├── utils/
│   ├── apiClient.js         — axios wrapper (`callApi`)
│   ├── storage.js           — localStorage utility + KEYS constants
│   ├── encryption.js        — AES decryption utility
│   ├── helper.js            — misc helpers (delay, UTM, Google Events, redirect)
│   └── handleRedirectionAfterLogin.js — post-login routing logic
├── hooks/                   — useToast, useStepper, usePageTracking, useBackButtonLogout
├── events/clevertapEvents.js — CleverTap event push wrappers
└── lib/
    ├── clevertap.js         — CleverTap SDK init
    └── razorpay.js          — Razorpay e-mandate integration
```

**External Services**
- **Backend REST API** — called via `src/utils/apiClient.js` (base URL from env)
- **CleverTap** — analytics/event tracking (`clevertap-web-sdk`)
- **Google OAuth** — `@react-oauth/google`, used for login and email pre-fill
- **Razorpay** — e-mandate payment flow (`src/lib/razorpay.js`)
- **HyperVerge** — selfie/KYC SDK (loaded dynamically in `SelfieHyperVerge.jsx`)
- **Finbox** — bank statement fetching (`src/pages/Finbox.jsx`)
- **Digilocker** — Aadhaar KYC redirect flow
- **Google Analytics (GA4)** — `gtag` via `index.html` + `trackG4Events` helper
- **Microsoft Clarity** — session recording, injected in `index.html`
- **AWS S3 + CloudFront** — static hosting (deployed via CI/CD)

**Core Request Lifecycle**
1. User visits SPA → `AppRoutes` resolves path → `ProtectedRoutes` checks auth token from localStorage
2. Page component calls service functions in `userService.js` → `callApi` (axios) → backend REST API
3. Responses update Redux slices (`userSlice`, `appSlice`) persisted via `redux-persist`
4. Navigation proceeds through loan journey steps; `stepCheckerAPI` determines current route on reload

---

## ROUTES

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

## DATA_MODELS

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