# Manual Jira Ticket Creation

Use these values when creating the ticket manually in Jira.

## Fields

Project:
RamFincorp Backend

Issue Type:
Story

Summary:
Add partner-safe Bureau Decision API audit lookup endpoints

Priority:
P1

Assignee:
Asha Backend

Reporter:
Nikhil Product

Components:
Bureau Decision API, API Key Middleware, MySQL Logging

Labels:
ramfincorp-backend, bureau-decision, api-audit, support-tooling, test-fixture

Due Date:
Leave blank. Assignee fills after approval.

Repository:
/home/ubuntu/ramfincorp-backend

## Description

Copy everything below this line into the Jira Description field.

```text
Build support and partner audit lookup endpoints for the Bureau Decision wrapper in ramfincorp-backend.

The service already writes sanitized request and response rows to vendor_bureau_api_logs and tracks API key rate limits in api_rate_limits. Support teams need a safe way to search a partner's bureau-decision request by request_id, reference_id, user_id, client_id, processing_status, and date range without exposing PAN, mobile number, raw bureau payloads, or full API keys.

h2. Problem

When a partner reports that a bureau decision call failed, support currently needs database access or engineering help to inspect the existing vendor_bureau_api_logs rows. This slows reconciliation and creates unnecessary access to sensitive data.

h2. Scope

* Add authenticated read-only endpoints under /api/v1/ramfincorp/bureau-decision/audit.
* Reuse the existing API key validation flow and rate-limit headers.
* Return only sanitized log fields and masked api_key values.
* Allow partner keys to view only their own client_id logs.
* Allow support-admin keys to query across clients when the key metadata role is support_admin.
* Include pagination, status filtering, date filtering, and summary counts.

h2. Functional Requirements

h3. FR1: Lookup One Audit Row

Endpoint:
GET /api/v1/ramfincorp/bureau-decision/audit/:request_id

Behavior:
* Requires x-api-key.
* Validates the API key using the existing API key flow.
* Returns one sanitized audit row when found and authorized.
* Returns 404 when the request does not exist.
* Returns 403 when the request exists but belongs to another client_id.

h3. FR2: Search Audit Rows

Endpoint:
GET /api/v1/ramfincorp/bureau-decision/audit

Supported query params:
* client_id
* reference_id
* user_id
* processing_status
* from_date
* to_date
* page
* page_size

Rules:
* page defaults to 1.
* page_size defaults to 25.
* page_size must be capped at 100.
* Results must be sorted by created_at desc.
* Partner keys must only see rows for their own client_id.
* Support-admin keys may query all clients.

h3. FR3: Audit Stats

Endpoint:
GET /api/v1/ramfincorp/bureau-decision/audit/stats

Returns aggregate counts for the same filters:
* total
* success
* error
* rate_limited
* avg_processing_time_ms

h3. FR4: Privacy and Masking

The endpoint must never return:
* Full api_key
* PAN
* mobile_number
* bureau_raw_data
* Full upstream bureau payloads
* Full request headers

Masking format:
rf_live_1234567890abcdef -> rf_live_****cdef

If the key is shorter than 8 characters, return ****.

h3. FR5: Validation

Invalid query params return 400 with field-level errors.

Validation examples:
* page must be a positive integer.
* page_size must be between 1 and 100.
* from_date and to_date must be ISO dates.
* processing_status must be one of the existing processing status enum values.
* to_date must be greater than or equal to from_date.

h2. Acceptance Criteria

AC1: GET /api/v1/ramfincorp/bureau-decision/audit/:request_id returns one sanitized log row for the matching request_id when the caller is authorized for that client_id.

AC2: GET /api/v1/ramfincorp/bureau-decision/audit supports filters client_id, reference_id, user_id, processing_status, from_date, to_date, page, and page_size. page_size must default to 25 and cap at 100.

AC3: GET /api/v1/ramfincorp/bureau-decision/audit/stats returns total, success, error, rate_limited, and average processing time for the same filter set.

AC4: API responses never include PAN, mobile_number, bureau_raw_data, full x-api-key, or raw upstream bureau payloads.

AC5: Unauthorized client access to another client_id returns 403 with a stable error_code.

AC6: Missing or invalid x-api-key returns 401 and follows the existing wrapper error response shape.

AC7: Invalid filters return 400 with field-level validation errors.

AC8: All new queries use indexed columns from vendor_bureau_api_logs and must not perform unbounded scans.

AC9: Unit tests cover authorization, masking, filter validation, pagination, and status summary calculations.

AC10: Integration tests seed three log rows across two clients and prove client isolation.

h2. Technical Context

Relevant repo:
/home/ubuntu/ramfincorp-backend

Routes:
src/routes/bureauDecision.route.ts

Controller:
src/controllers/bureauDecision.controller.ts

Services:
src/services/bureauDecision.service.ts
src/services/apiKey.service.ts

Models:
src/database/mysql/bureauApiLog.ts
src/database/mysql/rateLimit.ts

Migrations:
migrations/20250807100001-create_api_rate_limits_table.js
migrations/20250807100002-create_bureau_api_logs_table.js

Validation style:
Joi validators in src/validations/bureauDecision.validator.ts

Auth style:
x-api-key validation through ApiKeyService and ApiKeyMiddleware

h2. Test Focus

* API key authorization and client isolation
* PII masking and sanitized response shape
* Joi validation for query filters
* Knex query pagination and indexed filters
* Stats aggregation for processing statuses
* 404 behavior for unknown request_id

h2. Out of Scope

* Retrying or replaying bureau decision calls.
* Showing raw bureau report data.
* Modifying the bureau decision processing flow.
* CRM frontend changes.
```

