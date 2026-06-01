## ARCHITECTURE

```
ramfin-report (RamFin Reporting Service)
├── Entry Points
│   ├── src/start.ts          — process bootstrap
│   ├── src/server.ts         — instantiates App with all routes
│   └── src/app.ts            — Express App class; wires middleware, routes, DB connections
│
├── Config Layer
│   ├── src/config/default.ts         — default constants (IConfigApp)
│   ├── src/config/custom-environment-variables.ts — env var mappings
│   └── src/config.server.ts          — merges env vars into config singleton
│
├── Routes → Controllers → Services pattern
│   ├── routes/index.route.ts         — health/index
│   ├── routes/report.route.ts        — report endpoints
│   ├── routes/reportSummary.route.ts — report summary
│   ├── routes/quickReport.route.ts   — quick/async report download
│   └── routes/lead.route.ts          — lead modification report
│
├── Controllers (src/controllers/)
│   ├── index.controller.ts           — health check
│   ├── report.controller.ts          — sync report generation + Excel streaming
│   ├── reportSummary.controller.ts   — summary report
│   ├── quickReport.controller.ts     — queued async report download
│   ├── lead.controller.ts            — lead report endpoints
│   └── eventFunnel.controller.ts     — funnel analytics
│
├── Services (src/services/)
│   ├── report.service.ts             — all report query logic
│   ├── quickReport.service.ts        — quick report pagination, SQS job dispatch, S3 upload
│   ├── excelDownload.service.ts      — ExcelJS workbook generation
│   ├── lead.service.ts               — lead data queries
│   ├── loan.service.ts               — loan data, PDF generation (Puppeteer)
│   ├── emi.service.ts                — EMI calculation/queries
│   ├── credit.service.ts             — credit record management
│   ├── eventFunnel.service.ts        — funnel event queries
│   ├── notification.service.ts       — notification records
│   ├── teansections.services.ts      — transaction records
│   ├── api_req_res_log.service.ts    — API log persistence
│   ├── response.service.ts           — base response class
│   ├── api.service.ts                — Axios HTTP client wrapper
│   └── thirdParty/s3.service.ts      — AWS S3 + SES operations
│
├── Database Layer (src/database/)
│   ├── mysql/   — Knex-based model classes (primary + replica connections)
│   └── mongo/   — Mongoose model (OtpLogs)
│
├── Middlewares — auth (JWT), permission, pagination, validation (Joi), error, response
│
└── External Services
    ├── MySQL (primary + read replica)  — all core business data
    ├── MongoDB                          — OTP logs
    ├── AWS S3                           — report file storage, document storage
    ├── AWS SES                          — email sending
    └── AWS SQS                          — async quick-report job queue
```

Key lifecycle: HTTP request → Auth middleware → Permission check → Validation → Controller → Service → Knex/MySQL query or SQS dispatch → Excel/CSV/JSON response (or S3 upload + presigned URL).

---

## ROUTES

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

## DATA_MODELS

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