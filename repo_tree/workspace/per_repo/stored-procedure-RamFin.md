## ARCHITECTURE
This repository is a pure collection of MySQL stored procedures for RamFin's loan management platform. There is no application server, ORM, or service layer — all logic is expressed as `CREATE PROCEDURE` DDL statements.

**Storage Backend: Single MySQL database (`ramfin`)**
- Cross-database reference to `dsa` schema (DSA user management)

**Procedure Categories:**

- **Lead & Onboarding Reports**
  - `All_leads`, `get_lead_data`, `leads_not_completed_status_report_data`, `NotCompletedReport`, `event_funnel_report`, `event_funnel_reports`, `event_funnel_report_generate`, `user_funnel`, `event_data`
  - `api_log_data_with_error`, `get_journey_logs` (API monitoring)

- **Disbursal Reports**
  - `get_disbursal_data`, `get_disbursal_data_account`, `get_disbursal_data_account_ava`, `get_disbursal_data_quick_report`, `disbursalAmount_asondate`
  - `sp_disbursal_attribution_report`

- **Collection Reports**
  - `get_collection_data`, `get_collection_data_report_dashboard`, `get_collection_data_report_dashboard_created_at`, `get_collection_data_report_dashboard_optimized`
  - `collection_summary`, `collection_summary_aa`, `collection_summary_dd`, `collection_summary_nnew`, `collection_summarya`
  - `CollectionCityWiseProcedure`, `CollectionCreditmanagerWiseProcedure`, `CollectionSanctionalmanagerWiseProcedure`
  - `emi_collection_summary`, `collection_emi_data`, `emi_loan_collection_detail`
  - `pending_collection_summary_report`, `update_collection_calculations`

- **Loan Book / AUM**
  - `get_loan_book_data`, `get_loan_book_data_aum`, `get_loan_book_data_withemi`, `get_loan_book_data_withemi_specific`
  - `get_loan_book_data_withemi_static`, `get_loan_book_data_withemi_static_90`, `get_loan_book_data_withemi_static90`
  - `GetLoanbookSummaryRange`, `fy_monthly_summary`

- **Pending/Overdue Reports**
  - `payday_pending_report`, `payday_pending_report_phone`, `payday_pending_report_optimized`
  - `payday_pending_emi_report`, `payday_pending_emi_report_phone`, `datewise_payday_pending`, `DateWiseEMI`

- **DSA/Partner Reports**
  - `dsa_partner_data_as_disbursal`, `dsa_partner_data_as_disbursal_billing`, `dsa_partner_data_as_leads`, `dsa_partner_data_as_leads_new`, `dsa_partner_data_list`
  - `dsa_userwise_report`, `dsa_userwise_report_new`, `dsa_userwise_report_opt`
  - `agent_dsa_report`, `sp_lead_status_report`, `sp_lead_status_count_report`

- **Credit/Rejection/DPD Reports**
  - `CreditReportNewCasesProcedure`, `CreditReportRepeatCasesProcedure`, `rejection`, `repeat_dpd_report`, `repeat_dpd_reports`
  - `approved_process_transition`, `get_approval_process_counts_data`

- **Collection Status Procedures (Account-level)**
  - `ActualPaymentProcedure`, `ClosedAccountsProcedure`, `SettledAccountsProcedure`, `PartPayment`, `PendingAccountsProcedure`, `TotalLoanRepayment`, `TotalCasesProcedure`

- **Utility/Admin**
  - `grant_loanbook_access`, `GetCountsFromAllTables`, `update_all_timestamp_columns_with_logs`, `log_shifting_api_req_res_log`
  - `not_active_customer`, `mom_repeat_report`, `salaried_vs_self_employed_report`, `cibil_data_dump`, `settlement_data`

**External schema dependency:** `dsa.users`, `dsa.commission_slab`, `dsa.profile` (cross-database joins)

---

## ROUTES
No routes exposed. This repository contains only MySQL stored procedures; there is no HTTP server, RPC layer, or message queue consumer.

---

## DATA_MODELS
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
