## ARCHITECTURE

**Entry Point:** `src/main.jsx` → mounts React app with Redux `<Provider>`, `<PersistGate>`, Google OAuth `<GoogleOAuthProvider>`, and registers PWA service worker.

**Top-level modules:**
```
src/
├── main.jsx                  # App bootstrap, Redux/Google/PWA init
├── App.jsx                   # Root component, wraps AppRoutes
├── routes/
│   ├── AppRoutes.jsx         # React Router route definitions, InactivityLogout
│   └── ProtectedRoutes.jsx   # Auth guard wrapper
├── pages/                    # Full-page route components (20+ pages)
├── components/               # Reusable UI components (forms, shared, modals)
├── redux/
│   ├── store.js              # Redux store with redux-persist (whitelist: user, app)
│   └── slices/
│       ├── appSlice.js       # Global loading state, stepper flags, PWA trigger
│       └── userSlice.js      # Auth/session state (mobile, lead, customer, loan offer)
├── services/
│   └── userService.js        # All API call functions (axios via apiClient)
├── utils/
│   ├── apiClient.js          # Axios wrapper (callApi)
│   ├── encryption.js         # AES decrypt utility
│   ├── helper.js             # Delay, redirect, UTM, geolocation helpers
│   ├── storage.js            # localStorage wrapper + KEYS constants
│   └── validation.js         # Yup validation schemas
├── events/
│   └── clevertapEvents.js    # All CleverTap analytics event functions
├── i18n/                     # i18next config + en/hi/ka locale JSONs
├── lib/
│   ├── clevertap.js          # CleverTap SDK init
│   └── razorpay.js           # Razorpay e-mandate integration
└── hooks/                    # Custom React hooks
```

**External Services:**
- **Backend API** (`VITE_BASE_URL`) — Node.js onboarding API (loan journey steps)
- **PHP API** (`VITE_PHP_BASE_URL`) — legacy PHP backend
- **User Service** (`VITE_USER_SERVICE_BASE_URL`) — customer/auth service
- **Razorpay** — e-mandate payment
- **CleverTap** — analytics/event tracking
- **Digilocker / HyperVerge** — KYC verification
- **Finbox** — financial profile / bank statement analysis
- **Google OAuth** — email sign-in
- **AWS S3 + CloudFront** — static hosting (deployed via GitHub Actions)
- **Google Tag Manager / Meta Pixel / Microsoft Clarity** — analytics tags in `index.html`

**Core request lifecycle:** User action → Page component → `userService.js` function → `callApi()` (axios) → Backend API → Redux dispatch to update `userSlice`/`appSlice` → navigate to next route.

---

## ROUTES

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

## DATA_MODELS

No ORM or database models exist in this frontend repository. All persistent state is managed via Redux + `redux-persist` (localStorage).

**In-memory / Redux state (localStorage via redux-persist)**

`appSlice`  (src/redux/slices/appSlice.js) — fields: `loading.status`, `loading.message`, `stepperDisable`, `triggerInstallOnce`

`userSlice`  (src/redux/slices/userSlice.js) — fields: `mobile`, `requestId`, `customer`, `lead`, `employment`, `accountId`, `selectedLoanOffer`, `hasLoanOffer`, `upgradeLoanAmount`, `month12Clicked`, `isNewDigilocker`

**LocalStorage keys** (src/utils/storage.js) — `KEYS` object; specific key names unclear from source (skeletonized), but includes: `JWT_TOKEN`, `ACCESS_TOKEN`, `LEAD_ID` (referenced in service file comments)

**i18n locale schemas** (src/i18n/locales/en.json, hi.json, ka.json) — Not DB models; UI string maps for English, Hindi, Kannada. Keys cover: `login`, `panVerify`, `employmentDetails`, `selectLoanOffer`, `loanApproval`, `yourEmail`, `aadhaarVerification`, `cameraPermission`, `selfie`, `addBankAccount`, `pennyDrop`, `kfs`, `disbursed`, `loanRejected`, `finboxError`, `loaderMsg`, plus validation namespaces.