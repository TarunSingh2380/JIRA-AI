# PRD: Bureau Decision API Audit Lookup

## Document Control

- Jira ticket: RAM-BE-9001
- Repository: ramfincorp-backend
- Created: 2026-06-11
- Owner: Nikhil Product
- Engineering owner: Asha Backend
- Status: Draft for JIRA-AI testing

## Summary

Add read-only audit lookup endpoints for the Bureau Decision wrapper API so support and trusted partners can investigate request outcomes without direct database access or exposure to sensitive bureau data.

The backend already writes sanitized bureau API records to `vendor_bureau_api_logs` and tracks rate limits in `api_rate_limits`. This PRD asks engineering to expose those existing records through authenticated, scoped, paginated, and privacy-safe endpoints.

## Problem

When a partner reports a failed bureau-decision call, support currently needs engineering help or database access to inspect the request. That creates three problems:

- Slower partner reconciliation and issue resolution.
- Unnecessary operational dependency on engineers.
- Higher privacy risk because raw database access can reveal data that support does not need.

## Goals

- Let a partner or support user look up a bureau-decision request by `request_id`.
- Let support search sanitized logs by `reference_id`, `user_id`, `client_id`, status, and date range.
- Preserve strict client isolation for partner API keys.
- Prevent sensitive fields from being returned in every response.
- Reuse existing backend patterns in `ramfincorp-backend`.

## Non-Goals

- Do not retry or replay bureau decision calls.
- Do not expose full PAN, mobile number, raw bureau reports, upstream bureau payloads, or full API keys.
- Do not change the existing bureau decision processing behavior.
- Do not build frontend screens in this ticket.

## Users

- Partner operations team: checks its own request status during reconciliation.
- RamFincorp support team: investigates partner complaints and failed requests.
- Backend engineering: uses audit endpoints during incident triage without manually querying MySQL.

## Existing Code Context

- Route registration: `src/routes/bureauDecision.route.ts`
- Controller: `src/controllers/bureauDecision.controller.ts`
- Bureau service: `src/services/bureauDecision.service.ts`
- API key service: `src/services/apiKey.service.ts`
- Log model: `src/database/mysql/bureauApiLog.ts`
- Rate-limit model: `src/database/mysql/rateLimit.ts`
- Validation style: `src/validations/bureauDecision.validator.ts`
- Log table migration: `migrations/20250807100002-create_bureau_api_logs_table.js`
- Rate-limit table migration: `migrations/20250807100001-create_api_rate_limits_table.js`

## Functional Requirements

### FR1: Lookup One Audit Row

Endpoint:

```text
GET /api/v1/ramfincorp/bureau-decision/audit/:request_id
```

Behavior:

- Requires `x-api-key`.
- Validates the API key using the existing API key flow.
- Returns one sanitized audit row when found and authorized.
- Returns `404` when the request does not exist.
- Returns `403` when the request exists but belongs to another `client_id`.

Response fields:

- `request_id`
- `client_id`
- `user_id`
- `reference_id`
- `endpoint`
- `method`
- `processing_status`
- `http_status_code`
- `processing_time_ms`
- `error_code`
- `error_message`
- `workflow_version`
- `created_at`
- `request_data`
- `response_data`
- `api_key_masked`

### FR2: Search Audit Rows

Endpoint:

```text
GET /api/v1/ramfincorp/bureau-decision/audit
```

Supported query params:

- `client_id`
- `reference_id`
- `user_id`
- `processing_status`
- `from_date`
- `to_date`
- `page`
- `page_size`

Rules:

- `page` defaults to `1`.
- `page_size` defaults to `25`.
- `page_size` must be capped at `100`.
- Results must be sorted by `created_at desc`.
- Partner keys must only see rows for their own `client_id`.
- Support-admin keys may query all clients.

### FR3: Audit Stats

Endpoint:

```text
GET /api/v1/ramfincorp/bureau-decision/audit/stats
```

Returns aggregate counts for the same filters:

- `total`
- `success`
- `error`
- `rate_limited`
- `avg_processing_time_ms`

### FR4: Privacy and Masking

The endpoint must never return:

- Full `api_key`
- `pan`
- `mobile_number`
- `bureau_raw_data`
- Full upstream bureau payloads
- Full request headers

Masking format:

```text
rf_live_1234567890abcdef -> rf_live_****cdef
```

If the key is shorter than 8 characters, return `****`.

### FR5: Validation

Invalid query params return `400` with field-level errors.

Validation examples:

- `page` must be a positive integer.
- `page_size` must be between `1` and `100`.
- `from_date` and `to_date` must be ISO dates.
- `processing_status` must be one of the existing processing status enum values.
- `to_date` must be greater than or equal to `from_date`.

## Authorization Rules

- Missing or invalid `x-api-key`: return `401`.
- Partner key querying its own `client_id`: allow.
- Partner key querying another `client_id`: return `403`.
- Partner key omitting `client_id`: force filter to its own `client_id`.
- Support-admin key with metadata role `support_admin`: allow all clients.

## API Examples

Lookup:

```bash
curl -s \
  -H "x-api-key: rf_test_partner_alpha_key" \
  "http://localhost:3000/api/v1/ramfincorp/bureau-decision/audit/req_9001_success"
```

Search:

```bash
curl -s \
  -H "x-api-key: rf_test_partner_alpha_key" \
  "http://localhost:3000/api/v1/ramfincorp/bureau-decision/audit?processing_status=success&page=1&page_size=25"
```

Stats:

```bash
curl -s \
  -H "x-api-key: rf_test_support_admin_key" \
  "http://localhost:3000/api/v1/ramfincorp/bureau-decision/audit/stats?client_id=partner_alpha&from_date=2026-06-01T00:00:00Z"
```

## Acceptance Criteria

1. Given a valid partner API key, when the caller requests a `request_id` owned by the same `client_id`, then the API returns `200` with one sanitized row.
2. Given a valid partner API key, when the caller requests another client's `request_id`, then the API returns `403`.
3. Given an invalid API key, when the caller searches audit logs, then the API returns `401` using the existing wrapper error shape.
4. Given no pagination params, when the caller searches audit logs, then `page=1` and `page_size=25` are applied.
5. Given `page_size=500`, when the caller searches audit logs, then validation returns `400`.
6. Given seeded rows across two clients, when partner Alpha searches without `client_id`, then only partner Alpha rows are returned.
7. Given seeded success, error, and rate-limited rows, when stats are requested, then aggregate counts match the filtered dataset.
8. Given a row with sensitive request fields, when the row is returned, then PAN, mobile number, bureau raw data, and full API key are absent.
9. Given an unknown `request_id`, when lookup is requested, then the API returns `404`.
10. Given a support-admin API key, when `client_id=partner_beta` is provided, then partner Beta rows are returned.

## Test Plan

- Unit test the query validator for valid filters, invalid dates, invalid page values, and invalid statuses.
- Unit test API key masking.
- Unit test service authorization for partner keys and support-admin keys.
- Unit test response sanitization against request and response payloads containing PAN, mobile, and bureau raw data.
- Integration test search with three seeded `vendor_bureau_api_logs` rows across two clients.
- Integration test lookup by `request_id`.
- Integration test stats aggregation.
- Regression test existing `POST /api/v1/ramfincorp/bureau-decision` still processes requests as before.

## Suggested Implementation Notes

- Add query validators to `src/validations/bureauDecision.validator.ts`.
- Add route handlers in `src/routes/bureauDecision.route.ts`.
- Add controller methods to `src/controllers/bureauDecision.controller.ts`.
- Add read-only service methods to `src/services/bureauDecision.service.ts`.
- Extend `src/database/mysql/bureauApiLog.ts` with filtered search/count helpers if existing methods are not enough.
- Use indexed fields already present on `vendor_bureau_api_logs`: `client_id`, `created_at`, `processing_status`, `api_key`, and `error_code`.

## Rollout

- Deploy behind existing API key authentication.
- Smoke test in staging with seeded rows.
- Share endpoint examples with support.
- Monitor query latency and 4xx rates for one week after release.

