# 05_API_Contracts.md

# MoneyScope — API Contracts

> **Version:** 1.0.0
> **Status:** API Contract Definition
> **Backend:** FastAPI
> **Frontend:** React 19 + TanStack Start
> **API Style:** REST
> **API Version:** `/api/v1`
> **Database:** PostgreSQL
> **Authentication:** Bearer Token
> **Primary Currency:** INR

---

# 1. Purpose

This document defines the API contract between the MoneyScope frontend and backend.

It specifies:

* API routes
* HTTP methods
* Request parameters
* Request bodies
* Response structures
* Authentication requirements
* Validation rules
* Error responses
* Pagination
* Filtering
* Sorting
* Financial data conventions
* Idempotency
* API versioning

The frontend and backend should use this document as the shared contract.

---

# 2. API Architecture

The frontend communicates with FastAPI through REST APIs.

```text
React / TanStack Start
        │
        │ HTTPS
        ▼
FastAPI
        │
        ▼
Service Layer
        │
        ▼
Repository Layer
        │
        ▼
PostgreSQL
```

The frontend must never directly access PostgreSQL.

---

# 3. Base URL

Development:

```text
http://localhost:8000
```

API:

```text
http://localhost:8000/api/v1
```

Production:

```text
https://api.<production-domain>/api/v1
```

The exact production domain will be defined during deployment.

---

# 4. API Versioning

All V1 APIs use:

```text
/api/v1
```

Example:

```text
GET /api/v1/transactions
```

Future breaking changes:

```text
/api/v2
```

Existing V1 clients should continue to work until V1 is formally deprecated.

---

# 5. HTTP Methods

MoneyScope follows standard REST semantics.

| Method | Purpose                          |
| ------ | -------------------------------- |
| GET    | Retrieve data                    |
| POST   | Create resource / execute action |
| PATCH  | Partially update resource        |
| DELETE | Remove/archive resource          |

For financial records, `DELETE` should generally result in archival rather than permanent deletion.

---

# 6. Authentication

Protected APIs require:

```http
Authorization: Bearer <access_token>
```

Example:

```http
GET /api/v1/transactions
Authorization: Bearer eyJ...
```

The backend obtains the authenticated user from the token.

The frontend should not send:

```text
user_id
```

as a trusted ownership parameter for normal user-scoped APIs.

The backend determines the user from authentication.

---

# 7. Public vs Protected APIs

## Public

Potentially public:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/news
```

## Protected

Most financial APIs:

```text
/dashboard
/transactions
/accounts
/budgets
/goals
/investments
/analytics
/reports
/notifications
/settings
```

---

# 8. Common Headers

Request:

```http
Content-Type: application/json
Authorization: Bearer <token>
```

For file upload:

```http
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

Optional request tracing:

```http
X-Request-ID: <uuid>
```

The backend should generate a request ID if the client does not provide one.

---

# 9. Response Format

Successful responses should use predictable JSON structures.

For a single resource:

```json
{
  "data": {
    "id": "uuid",
    "name": "Emergency Fund"
  }
}
```

For collections:

```json
{
  "data": [
    {}
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

For dashboard/analytics responses where the payload is already a structured object:

```json
{
  "data": {
    "month_spent": "32000.00",
    "month_income": "60000.00"
  }
}
```

---

# 10. Error Response

All API errors should follow a consistent structure.

```json
{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction could not be found.",
    "details": null,
    "request_id": "uuid"
  }
}
```

---

# 11. Validation Error

For request validation:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": {
      "amount": [
        "Amount must be greater than zero."
      ]
    },
    "request_id": "uuid"
  }
}
```

---

# 12. Standard HTTP Status Codes

| Status | Meaning                                  |
| -----: | ---------------------------------------- |
|    200 | Successful request                       |
|    201 | Resource created                         |
|    202 | Accepted for background processing       |
|    204 | Successful request with no response body |
|    400 | Bad request                              |
|    401 | Authentication required                  |
|    403 | Permission denied                        |
|    404 | Resource not found                       |
|    409 | Conflict / duplicate                     |
|    422 | Validation failure                       |
|    429 | Rate limit exceeded                      |
|    500 | Internal server error                    |
|    502 | External provider failure                |
|    503 | Service temporarily unavailable          |

---

# 13. Authentication APIs

## 13.1 Register

```http
POST /api/v1/auth/register
```

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "display_name": "Suraj"
}
```

### Response

```http
201 Created
```

```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "display_name": "Suraj"
    }
  }
}
```

---

# 14. Login

```http
POST /api/v1/auth/login
```

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

### Response

```json
{
  "data": {
    "access_token": "token",
    "refresh_token": "token",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

# 15. Refresh Token

```http
POST /api/v1/auth/refresh
```

### Request

```json
{
  "refresh_token": "token"
}
```

### Response

```json
{
  "data": {
    "access_token": "new-token",
    "refresh_token": "new-token",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

# 16. Logout

```http
POST /api/v1/auth/logout
```

### Response

```http
204 No Content
```

The refresh token should be revoked server-side.

---

# 17. Current User

```http
GET /api/v1/auth/me
```

### Response

```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Suraj"
  }
}
```

---

# 18. User Profile

## Get Profile

```http
GET /api/v1/settings/profile
```

### Response

```json
{
  "data": {
    "user_id": "uuid",
    "display_name": "Suraj",
    "email": "user@example.com",
    "currency": "INR",
    "timezone": "Asia/Kolkata",
    "avatar_url": null
  }
}
```

---

# 19. Update Profile

```http
PATCH /api/v1/settings/profile
```

### Request

```json
{
  "display_name": "Suraj Sakhare",
  "avatar_url": null
}
```

### Response

```json
{
  "data": {
    "user_id": "uuid",
    "display_name": "Suraj Sakhare",
    "email": "user@example.com",
    "currency": "INR",
    "timezone": "Asia/Kolkata"
  }
}
```

---

# 20. User Preferences

## Get

```http
GET /api/v1/settings/preferences
```

### Response

```json
{
  "data": {
    "theme": "dark",
    "currency": "INR",
    "timezone": "Asia/Kolkata",
    "overspending_alerts_enabled": true,
    "bill_reminders_enabled": true,
    "goal_notifications_enabled": true,
    "monthly_report_enabled": true
  }
}
```

---

# 21. Update Preferences

```http
PATCH /api/v1/settings/preferences
```

### Request

```json
{
  "theme": "dark",
  "overspending_alerts_enabled": true,
  "bill_reminders_enabled": true,
  "goal_notifications_enabled": true
}
```

---

# 22. Accounts

Accounts represent where money is held.

Examples:

```text
HDFC Savings
ICICI Savings
Cash
Credit Card
Wallet
```

---

# 23. List Accounts

```http
GET /api/v1/accounts
```

### Query Parameters

```text
status
account_type
page
page_size
```

Example:

```text
GET /api/v1/accounts?status=active
```

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "HDFC Savings",
      "account_type": "BANK",
      "institution_name": "HDFC Bank",
      "currency": "INR",
      "current_balance": "42500.00",
      "is_active": true
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

---

# 24. Create Account

```http
POST /api/v1/accounts
```

### Request

```json
{
  "name": "HDFC Savings",
  "account_type": "BANK",
  "institution_name": "HDFC Bank",
  "currency": "INR"
}
```

### Response

```http
201 Created
```

---

# 25. Get Account

```http
GET /api/v1/accounts/{account_id}
```

---

# 26. Update Account

```http
PATCH /api/v1/accounts/{account_id}
```

Example:

```json
{
  "name": "HDFC Salary Account"
}
```

---

# 27. Archive Account

```http
DELETE /api/v1/accounts/{account_id}
```

The backend should archive the account rather than delete historical transactions.

### Response

```http
204 No Content
```

---

# 28. Transactions

Transactions are the primary financial event resource.

---

# 29. List Transactions

```http
GET /api/v1/transactions
```

### Query Parameters

```text
search
account_id
category_id
transaction_type
payment_provider
source

from_date
to_date

page
page_size

sort_by
sort_order
```

Example:

```text
GET /api/v1/transactions?from_date=2026-08-01&to_date=2026-08-31&page=1&page_size=20
```

---

# 30. Transaction Response

```json
{
  "data": [
    {
      "id": "uuid",
      "account_id": "uuid",
      "category": {
        "id": "uuid",
        "name": "Food"
      },
      "merchant": {
        "id": "uuid",
        "name": "Swiggy"
      },
      "amount": "450.00",
      "transaction_type": "EXPENSE",
      "direction": "DEBIT",
      "payment_provider": "PhonePe",
      "source": "MANUAL",
      "occurred_at": "2026-08-11T14:30:00Z",
      "description": null,
      "created_at": "2026-08-11T14:30:02Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

---

# 31. Create Transaction

```http
POST /api/v1/transactions
```

### Request

```json
{
  "account_id": "uuid",
  "category_id": "uuid",
  "merchant_name": "Swiggy",
  "amount": "450.00",
  "transaction_type": "EXPENSE",
  "direction": "DEBIT",
  "payment_provider": "PhonePe",
  "occurred_at": "2026-08-11T14:30:00+05:30",
  "description": "Lunch",
  "source": "MANUAL"
}
```

### Response

```http
201 Created
```

---

# 32. Transaction Business Rules

The backend must validate:

```text
amount > 0
```

For:

```text
EXPENSE
INVESTMENT
TRANSFER
```

the direction is generally:

```text
DEBIT
```

For:

```text
INCOME
REFUND
```

the direction is generally:

```text
CREDIT
```

The service layer should reject logically invalid combinations.

---

# 33. Get Transaction

```http
GET /api/v1/transactions/{transaction_id}
```

The backend must verify that the transaction belongs to the authenticated user.

---

# 34. Update Transaction

```http
PATCH /api/v1/transactions/{transaction_id}
```

Example:

```json
{
  "category_id": "uuid",
  "merchant_name": "Swiggy",
  "description": "Dinner"
}
```

The backend must carefully handle changes to:

* amount
* account
* transaction type
* direction

because these can affect balances and analytics.

---

# 35. Archive Transaction

```http
DELETE /api/v1/transactions/{transaction_id}
```

This should normally soft-delete/archive the transaction.

Historical audit information should be preserved.

---

# 36. Transaction Import

```http
POST /api/v1/transactions/import
```

Content type:

```text
multipart/form-data
```

Fields:

```text
file
source_type
account_id
dry_run
```

Example:

```text
source_type=CSV
account_id=<uuid>
dry_run=false
```

---

# 37. Import Response

For asynchronous processing:

```http
202 Accepted
```

```json
{
  "data": {
    "job_id": "uuid",
    "status": "PENDING"
  }
}
```

---

# 38. Import Job Status

```http
GET /api/v1/transactions/import/{job_id}
```

### Response

```json
{
  "data": {
    "job_id": "uuid",
    "status": "PROCESSING",
    "total_rows": 1000,
    "accepted_rows": 720,
    "rejected_rows": 30,
    "duplicate_rows": 250
  }
}
```

---

# 39. Categories

## List Categories

```http
GET /api/v1/categories
```

### Query

```text
type=EXPENSE
```

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Food",
      "type": "EXPENSE",
      "is_system": true
    }
  ]
}
```

---

# 40. Create Category

```http
POST /api/v1/categories
```

### Request

```json
{
  "name": "Gym",
  "type": "EXPENSE"
}
```

---

# 41. Update Category

```http
PATCH /api/v1/categories/{category_id}
```

---

# 42. Archive Category

```http
DELETE /api/v1/categories/{category_id}
```

A category referenced by transactions should be archived rather than physically deleted.

---

# 43. Budgets

## List Budgets

```http
GET /api/v1/budgets
```

### Query

```text
month
year
status
```

---

# 44. Create Budget

```http
POST /api/v1/budgets
```

### Request

```json
{
  "name": "August Budget",
  "period_type": "MONTHLY",
  "start_date": "2026-08-01",
  "end_date": "2026-08-31",
  "amount": "30000.00"
}
```

---

# 45. Budget Response

```json
{
  "data": {
    "id": "uuid",
    "name": "August Budget",
    "amount": "30000.00",
    "spent": "21000.00",
    "remaining": "9000.00",
    "utilization_pct": 70.0,
    "start_date": "2026-08-01",
    "end_date": "2026-08-31"
  }
}
```

`spent`, `remaining`, and `utilization_pct` are derived values.

---

# 46. Budget Categories

## Add Category Budget

```http
POST /api/v1/budgets/{budget_id}/categories
```

### Request

```json
{
  "category_id": "uuid",
  "amount": "5000.00"
}
```

---

# 47. Update Category Budget

```http
PATCH /api/v1/budgets/{budget_id}/categories/{budget_category_id}
```

---

# 48. Remove Category Budget

```http
DELETE /api/v1/budgets/{budget_id}/categories/{budget_category_id}
```

---

# 49. Goals

## List Goals

```http
GET /api/v1/goals
```

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Emergency Fund",
      "target_amount": "100000.00",
      "saved_amount": "45000.00",
      "remaining_amount": "55000.00",
      "progress_pct": 45.0,
      "deadline": "2027-01-01",
      "status": "ACTIVE",
      "icon_key": "shield",
      "color_key": "blue"
    }
  ]
}
```

---

# 50. Create Goal

```http
POST /api/v1/goals
```

### Request

```json
{
  "name": "Emergency Fund",
  "target_amount": "100000.00",
  "deadline": "2027-01-01",
  "icon_key": "shield",
  "color_key": "blue"
}
```

---

# 51. Get Goal

```http
GET /api/v1/goals/{goal_id}
```

---

# 52. Update Goal

```http
PATCH /api/v1/goals/{goal_id}
```

Example:

```json
{
  "target_amount": "150000.00",
  "deadline": "2027-03-01"
}
```

---

# 53. Add Goal Contribution

```http
POST /api/v1/goals/{goal_id}/contributions
```

### Request

```json
{
  "amount": "2000.00",
  "contributed_at": "2026-08-11T10:00:00+05:30",
  "note": "Monthly savings"
}
```

Optional transaction linkage:

```json
{
  "amount": "2000.00",
  "source_transaction_id": "uuid"
}
```

---

# 54. Goal Contribution Response

```json
{
  "data": {
    "contribution_id": "uuid",
    "goal_id": "uuid",
    "amount": "2000.00",
    "saved_amount": "47000.00",
    "remaining_amount": "53000.00",
    "progress_pct": 47.0
  }
}
```

---

# 55. Investments

## Portfolio Summary

```http
GET /api/v1/investments/portfolio
```

### Query

```text
range=12m
```

### Response

```json
{
  "data": {
    "invested_total": "150000.00",
    "current_value_total": "168500.00",
    "profit_loss": "18500.00",
    "profit_loss_pct": 12.33,
    "allocation": [
      {
        "asset_type": "MUTUAL_FUND",
        "value": "100000.00",
        "percentage": 59.35
      }
    ],
    "series": [
      {
        "date": "2026-01-01",
        "value": "140000.00"
      }
    ]
  }
}
```

---

# 56. Investment Holdings

```http
GET /api/v1/investments/holdings
```

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Example Mutual Fund",
      "asset_type": "MUTUAL_FUND",
      "invested_amount": "50000.00",
      "current_value": "56000.00",
      "profit_loss": "6000.00",
      "return_pct": 12.0,
      "quantity": "125.50000000"
    }
  ]
}
```

---

# 57. Create Investment Holding

```http
POST /api/v1/investments/holdings
```

### Request

```json
{
  "name": "Example Mutual Fund",
  "asset_type": "MUTUAL_FUND",
  "invested_amount": "50000.00",
  "current_value": "50000.00",
  "quantity": "125.50000000",
  "average_cost": "398.4064"
}
```

---

# 58. Update Investment Holding

```http
PATCH /api/v1/investments/holdings/{holding_id}
```

---

# 59. Archive Investment Holding

```http
DELETE /api/v1/investments/holdings/{holding_id}
```

Historical investment snapshots must remain available.

---

# 60. Dashboard

Dashboard is a high-level aggregation API.

---

# 61. Dashboard Summary

```http
GET /api/v1/dashboard/summary
```

### Query Parameters

```text
month
year
timezone
```

Example:

```text
GET /api/v1/dashboard/summary?month=8&year=2026
```

### Response

```json
{
  "data": {
    "period": {
      "month": 8,
      "year": 2026
    },

    "today_spent": "850.00",
    "month_spent": "32000.00",
    "month_income": "60000.00",

    "monthly_budget": "40000.00",
    "budget_remaining": "8000.00",
    "budget_utilization_pct": 80.0,

    "safe_to_spend": "12000.00",

    "savings": "20000.00",
    "savings_rate_pct": 33.33,

    "financial_health_score": 78,

    "invested_total": "150000.00",
    "portfolio_value": "168500.00",
    "portfolio_change_pct": 12.33
  }
}
```

---

# 62. Dashboard Trend

```http
GET /api/v1/dashboard/trend
```

### Query

```text
from_date
to_date
group_by=day
```

### Response

```json
{
  "data": [
    {
      "date": "2026-08-01",
      "expense": "1200.00",
      "income": "0.00"
    },
    {
      "date": "2026-08-02",
      "expense": "850.00",
      "income": "0.00"
    }
  ]
}
```

---

# 63. Dashboard Category Breakdown

```http
GET /api/v1/dashboard/category-breakdown
```

### Response

```json
{
  "data": [
    {
      "category_id": "uuid",
      "category": "Food",
      "amount": "8500.00",
      "percentage": 26.56
    }
  ]
}
```

---

# 64. Dashboard Recent Transactions

```http
GET /api/v1/dashboard/recent-transactions
```

### Query

```text
limit=6
```

Maximum limit should be enforced server-side.

---

# 65. Dashboard Alerts

```http
GET /api/v1/dashboard/alerts
```

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "type": "BUDGET_WARNING",
      "title": "Food budget is almost full",
      "message": "You have used 85% of your food budget.",
      "actionable": true,
      "created_at": "2026-08-11T12:00:00Z"
    }
  ]
}
```

---

# 66. Composite Dashboard API

Optional optimization:

```http
GET /api/v1/dashboard
```

This may return:

```text
summary
trend
category_breakdown
recent_transactions
goals_preview
alerts
```

The composite endpoint should be introduced only if multiple requests become a measurable performance issue.

The individual endpoints remain useful for independent loading and caching.

---

# 67. Analytics

Analytics provides deeper financial insights.

---

# 68. Spending Overview

```http
GET /api/v1/analytics/spending-overview
```

### Query

```text
from_date
to_date
group_by=day
```

### Response

```json
{
  "data": {
    "total_spent": "32000.00",
    "average_daily_spend": "1032.26",
    "trend": [
      {
        "date": "2026-08-01",
        "amount": "1200.00"
      }
    ]
  }
}
```

---

# 69. Category Analytics

```http
GET /api/v1/analytics/categories
```

### Response

```json
{
  "data": [
    {
      "category": "Food",
      "amount": "8500.00",
      "percentage": 26.56
    },
    {
      "category": "Transport",
      "amount": "4500.00",
      "percentage": 14.06
    }
  ]
}
```

---

# 70. UPI / Payment Provider Analytics

This endpoint directly addresses the multi-UPI problem.

```http
GET /api/v1/analytics/payment-providers
```

### Response

```json
{
  "data": [
    {
      "provider": "PhonePe",
      "amount": "12000.00",
      "transaction_count": 18,
      "percentage": 37.5
    },
    {
      "provider": "GooglePay",
      "amount": "9000.00",
      "transaction_count": 15,
      "percentage": 28.13
    }
  ]
}
```

This allows the user to understand:

> "How much did I spend across all my UPI apps?"

rather than seeing each app separately.

---

# 71. Budget Analytics

```http
GET /api/v1/analytics/budget
```

### Response

```json
{
  "data": {
    "budget": "40000.00",
    "spent": "32000.00",
    "remaining": "8000.00",
    "utilization_pct": 80.0
  }
}
```

---

# 72. Financial Health

```http
GET /api/v1/analytics/financial-health
```

### Response

```json
{
  "data": {
    "score": 78,
    "version": 1,
    "factors": [
      {
        "name": "Savings Rate",
        "score": 82,
        "weight": 0.25
      },
      {
        "name": "Budget Control",
        "score": 74,
        "weight": 0.25
      }
    ],
    "recommendations": [
      "Reduce discretionary food spending by 10%."
    ]
  }
}
```

---

# 73. Safe-to-Spend

```http
GET /api/v1/analytics/safe-to-spend
```

### Response

```json
{
  "data": {
    "amount": "12000.00",
    "currency": "INR",
    "period": "2026-08",
    "explanation": {
      "available_funds": "25000.00",
      "upcoming_bills": "5000.00",
      "goal_commitments": "3000.00",
      "recommended_buffer": "5000.00"
    }
  }
}
```

The calculation must be performed by the backend.

---

# 74. Reports

## List Reports

```http
GET /api/v1/reports
```

---

# 75. Generate Monthly Report

```http
POST /api/v1/reports/monthly
```

### Request

```json
{
  "year": 2026,
  "month": 8
}
```

### Response

If asynchronous:

```http
202 Accepted
```

```json
{
  "data": {
    "report_id": "uuid",
    "status": "PROCESSING"
  }
}
```

---

# 76. Report Status

```http
GET /api/v1/reports/{report_id}
```

### Response

```json
{
  "data": {
    "id": "uuid",
    "status": "COMPLETED",
    "period_start": "2026-08-01",
    "period_end": "2026-08-31",
    "download_url": "signed-url"
  }
}
```

Signed URLs should expire.

---

# 77. Notifications

## List Notifications

```http
GET /api/v1/notifications
```

### Query

```text
is_read
page
page_size
```

---

# 78. Mark Notification Read

```http
PATCH /api/v1/notifications/{notification_id}
```

### Request

```json
{
  "is_read": true
}
```

---

# 79. Mark All Notifications Read

```http
POST /api/v1/notifications/mark-all-read
```

### Response

```http
204 No Content
```

---

# 80. News

News is a supporting product feature rather than a financial source of truth.

---

# 81. List News

```http
GET /api/v1/news
```

### Query Parameters

```text
tag
page
page_size
from_date
to_date
```

---

# 82. News Response

```json
{
  "data": {
    "hot": [
      {
        "id": "uuid",
        "title": "RBI announces...",
        "source": "Example News",
        "published_at": "2026-08-11T08:00:00Z",
        "tag": "RBI",
        "article_url": "https://example.com/article"
      }
    ],
    "items": [
      {
        "id": "uuid",
        "title": "Markets today...",
        "source": "Example News",
        "published_at": "2026-08-11T07:00:00Z",
        "tag": "Markets",
        "article_url": "https://example.com/article"
      }
    ]
  },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

# 83. News Tags

```http
GET /api/v1/news/tags
```

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Markets"
    },
    {
      "id": "uuid",
      "name": "RBI"
    },
    {
      "id": "uuid",
      "name": "Tax"
    }
  ]
}
```

---

# 84. Linked Providers

## List

```http
GET /api/v1/settings/linked-providers
```

---

# 85. Add Linked Provider

```http
POST /api/v1/settings/linked-providers
```

### Request

```json
{
  "provider_type": "UPI",
  "provider_name": "PhonePe",
  "display_name": "My PhonePe"
}
```

V1 may treat this as metadata only.

Direct UPI synchronization is out of scope unless an official supported integration exists.

---

# 86. Remove Linked Provider

```http
DELETE /api/v1/settings/linked-providers/{provider_id}
```

This should not delete historical transactions.

---

# 87. Pagination

Collection endpoints use:

```text
page
page_size
```

Example:

```text
?page=1&page_size=20
```

Recommended limits:

```text
default page_size = 20
maximum page_size = 100
```

The backend must enforce the maximum.

---

# 88. Pagination Response

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 250,
    "total_pages": 13
  }
}
```

---

# 89. Sorting

Supported query parameters:

```text
sort_by
sort_order
```

Example:

```text
sort_by=occurred_at
sort_order=desc
```

The backend should maintain an allow-list of sortable fields.

Never directly interpolate arbitrary client input into SQL ordering clauses.

---

# 90. Filtering

Filters must be explicit.

Example:

```text
GET /api/v1/transactions
    ?category_id=uuid
    &account_id=uuid
    &transaction_type=EXPENSE
    &payment_provider=PhonePe
```

Unknown filters should either be rejected with validation errors or ignored according to the API policy.

For V1, rejecting unsupported filters is preferable because it prevents silent client mistakes.

---

# 91. Date Filtering

Use ISO date formats.

Date:

```text
2026-08-01
```

Datetime:

```text
2026-08-01T10:30:00+05:30
```

The backend should normalize timestamps appropriately.

---

# 92. Monetary Values in JSON

Money should preferably be returned as strings.

Example:

```json
{
  "amount": "1250.50"
}
```

instead of:

```json
{
  "amount": 1250.5
}
```

Reason:

Avoid floating-point precision problems across languages and clients.

The frontend can convert values for display when required.

---

# 93. Percentage Values

Percentages can be returned as numbers.

Example:

```json
{
  "percentage": 72.35
}
```

The backend should define whether percentage values represent:

```text
0–100
```

or:

```text
0–1
```

MoneyScope V1 standard:

```text
0–100
```

---

# 94. API Idempotency

Operations that may be retried should support idempotency.

Potential endpoints:

```text
POST /transactions
POST /transactions/import
POST /goals/{id}/contributions
POST /reports/monthly
```

For supported endpoints:

```http
Idempotency-Key: <unique-key>
```

The backend can use the key to prevent accidental duplicate operations.

---

# 95. Idempotency Example

Suppose the frontend sends:

```text
POST /goals/{id}/contributions
```

with:

```http
Idempotency-Key: abc-123
```

If the request is retried:

```text
abc-123
```

must not create another contribution.

---

# 96. Optimistic UI

The frontend may use optimistic updates for low-risk UI changes.

Example:

```text
Mark notification as read
```

But financial mutations should generally wait for backend confirmation.

Examples:

```text
Create transaction
Add goal contribution
Update investment
```

The server response is authoritative.

---

# 97. Cache Invalidation

After creating a transaction:

```text
Invalidate:
transactions
dashboard
analytics
budget
financial-health
safe-to-spend
```

Conceptually:

```text
POST /transactions
        ↓
Transaction created
        ↓
Invalidate dependent queries
```

The exact TanStack Query keys will be defined in frontend integration.

---

# 98. Transaction Dependency Graph

```text
Transaction
    │
    ├── Dashboard
    ├── Analytics
    ├── Budget
    ├── Financial Health
    ├── Safe-to-Spend
    └── Reports
```

This dependency must be considered when implementing cache invalidation.

---

# 99. Goal Dependency Graph

```text
Goal Contribution
       │
       ├── Goal Progress
       ├── Dashboard
       ├── Financial Health
       └── Reports
```

---

# 100. Investment Dependency Graph

```text
Investment Holding
       │
       ├── Portfolio
       ├── Dashboard
       ├── Net Worth
       └── Financial Health
```

---

# 101. Authorization Rules

Every protected endpoint must enforce ownership.

Example:

```text
GET /api/v1/goals/{goal_id}
```

Backend:

```text
goal.user_id == current_user.id
```

If false:

```http
404 Not Found
```

Returning `404` instead of exposing that another user's resource exists is preferred.

---

# 102. Sensitive Operations

Some future operations may require additional authentication.

Examples:

* Change email
* Change password
* Export all financial data
* Delete account
* Link financial provider

These may require recent authentication or a verification step.

---

# 103. Account Balance API

Optional V1 endpoint:

```http
GET /api/v1/accounts/{account_id}/balance
```

### Response

```json
{
  "data": {
    "account_id": "uuid",
    "balance": "42500.00",
    "currency": "INR",
    "as_of": "2026-08-11T15:30:00Z"
  }
}
```

---

# 104. Financial Overview API

Optional aggregate endpoint:

```http
GET /api/v1/financial-overview
```

Potential response:

```json
{
  "data": {
    "total_cash": "65000.00",
    "total_investments": "168500.00",
    "total_liabilities": "25000.00",
    "net_worth": "208500.00"
  }
}
```

This can eventually become a major dashboard feature.

---

# 105. Future API — Recurring Expenses

Not required for V1, but architecture should support:

```text
GET    /api/v1/recurring-expenses
POST   /api/v1/recurring-expenses
PATCH  /api/v1/recurring-expenses/{id}
DELETE /api/v1/recurring-expenses/{id}
```

Potential use cases:

* Rent
* Subscriptions
* EMI
* Insurance
* SIP

---

# 106. Future API — Financial Targets

Future target planning may include:

```text
POST /api/v1/plans
GET  /api/v1/plans
PATCH /api/v1/plans/{id}
```

This could support:

```text
Emergency Fund
Travel
Car
House
Education
Retirement
```

The V1 Goals API provides the foundation.

---

# 107. Future API — AI Financial Insights

Future endpoint:

```text
GET /api/v1/insights
```

Potential response:

```json
{
  "data": [
    {
      "type": "SPENDING_ANOMALY",
      "title": "Food spending increased",
      "message": "Your food spending is 24% higher than your average.",
      "severity": "MEDIUM"
    }
  ]
}
```

AI should consume structured financial data through backend services.

The AI layer must not have direct database access.

---

# 108. Future API — Data Export

Future:

```http
POST /api/v1/export
```

Possible formats:

```text
CSV
JSON
PDF
```

Export operations may be asynchronous for large datasets.

---

# 109. API Security Rules

The backend must:

1. Authenticate protected requests.
2. Verify resource ownership.
3. Validate all input.
4. Rate-limit sensitive endpoints.
5. Never trust frontend calculations.
6. Never expose database credentials.
7. Never expose external API secrets.
8. Sanitize external URLs where appropriate.
9. Avoid leaking existence of another user's resources.
10. Log security-sensitive events.

---

# 110. API Error Codes

Recommended machine-readable codes:

```text
AUTH_INVALID_CREDENTIALS
AUTH_TOKEN_EXPIRED
AUTH_REFRESH_INVALID

VALIDATION_ERROR

RESOURCE_NOT_FOUND
RESOURCE_FORBIDDEN
RESOURCE_CONFLICT

ACCOUNT_NOT_FOUND
ACCOUNT_ARCHIVED

TRANSACTION_NOT_FOUND
TRANSACTION_DUPLICATE
TRANSACTION_INVALID_TYPE

IMPORT_NOT_FOUND
IMPORT_FAILED
IMPORT_DUPLICATE

BUDGET_NOT_FOUND
BUDGET_INVALID_PERIOD

GOAL_NOT_FOUND
GOAL_INVALID_AMOUNT
GOAL_ALREADY_COMPLETED

INVESTMENT_NOT_FOUND
INVESTMENT_INVALID_VALUE

REPORT_NOT_FOUND
REPORT_GENERATION_FAILED

NEWS_UNAVAILABLE

RATE_LIMIT_EXCEEDED

INTERNAL_ERROR
```

---

# 111. API Contract Example — Complete Transaction Flow

### Request

```http
POST /api/v1/transactions
Authorization: Bearer <token>
Content-Type: application/json
Idempotency-Key: transaction-123
```

```json
{
  "account_id": "account-uuid",
  "category_id": "food-category-uuid",
  "merchant_name": "Swiggy",
  "amount": "450.00",
  "transaction_type": "EXPENSE",
  "direction": "DEBIT",
  "payment_provider": "PhonePe",
  "occurred_at": "2026-08-11T14:30:00+05:30",
  "description": "Lunch",
  "source": "MANUAL"
}
```

### Backend

```text
Authenticate
     ↓
Validate request
     ↓
Validate account ownership
     ↓
Validate category
     ↓
Validate transaction type
     ↓
Check idempotency
     ↓
BEGIN
     ↓
Create transaction
     ↓
Update account balance if applicable
     ↓
Create audit event
     ↓
COMMIT
     ↓
Return transaction
```

### Response

```http
201 Created
```

```json
{
  "data": {
    "id": "transaction-uuid",
    "amount": "450.00",
    "transaction_type": "EXPENSE",
    "direction": "DEBIT",
    "payment_provider": "PhonePe",
    "occurred_at": "2026-08-11T14:30:00+05:30"
  }
}
```

---

# 112. API Contract Example — Monthly Analytics

```text
GET /api/v1/analytics/spending-overview
    ?from_date=2026-08-01
    &to_date=2026-08-31
    &group_by=day
```

Flow:

```text
Request
   ↓
Authentication
   ↓
Validate date range
   ↓
Analytics Service
   ↓
PostgreSQL aggregation
   ↓
Analytics response
   ↓
TanStack Query
   ↓
Recharts
```

The frontend should not download all transactions simply to create the chart.

---

# 113. API Contract Example — Multiple UPI Apps

This is one of MoneyScope's key product problems.

Suppose the user has:

```text
PhonePe
Google Pay
Paytm
```

The frontend requests:

```http
GET /api/v1/analytics/payment-providers
```

Backend returns:

```json
{
  "data": [
    {
      "provider": "PhonePe",
      "amount": "12000.00",
      "transaction_count": 18
    },
    {
      "provider": "GooglePay",
      "amount": "9000.00",
      "transaction_count": 15
    },
    {
      "provider": "Paytm",
      "amount": "4000.00",
      "transaction_count": 7
    }
  ]
}
```

The user can immediately see:

```text
Total UPI spending:
₹25,000
```

without manually checking three applications.

---

# 114. API Contract — Month-End Summary

A future monthly summary endpoint may be:

```http
GET /api/v1/reports/monthly-summary
?year=2026
&month=8
```

Response:

```json
{
  "data": {
    "income": "60000.00",
    "expenses": "32000.00",
    "investments": "8000.00",
    "savings": "20000.00",
    "savings_rate_pct": 33.33,

    "top_categories": [
      {
        "category": "Food",
        "amount": "8500.00"
      }
    ],

    "top_payment_providers": [
      {
        "provider": "PhonePe",
        "amount": "12000.00"
      }
    ],

    "budget": {
      "planned": "40000.00",
      "spent": "32000.00",
      "utilization_pct": 80.0
    }
  }
}
```

This directly solves the user's month-end question:

> **"Where did my money go this month?"**

---

# 115. API Contract — Financial Growth

Future financial growth endpoint:

```http
GET /api/v1/analytics/growth
```

Possible response:

```json
{
  "data": {
    "monthly_savings": [
      {
        "month": "2026-06",
        "amount": "15000.00"
      },
      {
        "month": "2026-07",
        "amount": "18000.00"
      },
      {
        "month": "2026-08",
        "amount": "20000.00"
      }
    ],
    "average_savings_rate_pct": 31.5,
    "growth_trend": "POSITIVE"
  }
}
```

This supports the long-term financial-growth direction of MoneyScope.

---

# 116. API Contract — Financial News

Financial news should remain separate from transaction APIs.

```text
GET /api/v1/news
```

The news service may later personalize content based on:

```text
User preferences
Investment interests
Financial goals
```

However, personalization must not compromise privacy.

---

# 117. API Contract — AI Layer

Future AI services should consume backend-defined structured data.

Preferred:

```text
FastAPI
   ↓
Insights Service
   ↓
Financial Data Service
   ↓
AI Provider
```

Not:

```text
AI Provider
   ↓
Direct PostgreSQL access
```

AI should receive only the minimum data required to generate an insight.

---

# 118. Frontend Integration Rules

The existing frontend should integrate through an API client layer.

Recommended:

```text
src/lib/api/
```

Example:

```text
src/lib/api/client.ts
src/lib/api/auth.ts
src/lib/api/transactions.ts
src/lib/api/dashboard.ts
src/lib/api/analytics.ts
src/lib/api/goals.ts
src/lib/api/investments.ts
src/lib/api/news.ts
src/lib/api/settings.ts
```

Avoid scattering raw `fetch()` calls throughout route components.

---

# 119. Frontend Query Organization

Conceptually:

```text
src/
 ├── lib/
 │    └── api/
 │         ├── client.ts
 │         ├── transactions.ts
 │         ├── dashboard.ts
 │         ├── analytics.ts
 │         ├── goals.ts
 │         ├── investments.ts
 │         └── news.ts
 │
 └── hooks/
      ├── use-transactions.ts
      ├── use-dashboard.ts
      ├── use-analytics.ts
      └── use-goals.ts
```

This keeps route components focused on UI.

---

# 120. API Contract Ownership

Backend owns:

* Financial calculations
* Authorization
* Database integrity
* Business rules
* API response correctness

Frontend owns:

* Presentation
* User interaction
* Loading states
* Error presentation
* Client-side form experience

Both sides share:

* API schema
* Validation expectations
* Error codes
* Resource naming

---

# 121. Contract Testing

The API contract should eventually be validated using:

* OpenAPI
* Pydantic schemas
* Integration tests
* Frontend TypeScript types

Ideally, frontend API types can eventually be generated from OpenAPI.

This reduces drift between:

```text
FastAPI
```

and:

```text
TypeScript
```

---

# 122. OpenAPI as the Technical Contract

FastAPI should expose OpenAPI documentation.

The API contract should remain aligned with:

```text
/openapi.json
```

The development process should be:

```text
API Contract
     ↓
Pydantic Schema
     ↓
FastAPI Endpoint
     ↓
OpenAPI
     ↓
Frontend Types
```

---

# 123. API Development Order

Implementation should follow domain dependencies.

Recommended order:

```text
1. Authentication
        ↓
2. Users / Settings
        ↓
3. Accounts
        ↓
4. Categories
        ↓
5. Transactions
        ↓
6. Budgets
        ↓
7. Dashboard
        ↓
8. Analytics
        ↓
9. Goals
        ↓
10. Investments
        ↓
11. Notifications
        ↓
12. Reports
        ↓
13. News
```

---

# 124. V1 Required APIs

The minimum V1 backend should implement:

## Authentication

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
```

## Accounts

```text
GET    /accounts
POST   /accounts
GET    /accounts/{id}
PATCH  /accounts/{id}
DELETE /accounts/{id}
```

## Categories

```text
GET    /categories
POST   /categories
PATCH  /categories/{id}
DELETE /categories/{id}
```

## Transactions

```text
GET    /transactions
POST   /transactions
GET    /transactions/{id}
PATCH  /transactions/{id}
DELETE /transactions/{id}

POST   /transactions/import
GET    /transactions/import/{job_id}
```

## Budgets

```text
GET    /budgets
POST   /budgets
PATCH  /budgets/{id}

POST   /budgets/{id}/categories
PATCH  /budgets/{id}/categories/{category_id}
DELETE /budgets/{id}/categories/{category_id}
```

## Dashboard

```text
GET /dashboard/summary
GET /dashboard/trend
GET /dashboard/category-breakdown
GET /dashboard/recent-transactions
GET /dashboard/alerts
```

## Analytics

```text
GET /analytics/spending-overview
GET /analytics/categories
GET /analytics/payment-providers
GET /analytics/budget
GET /analytics/financial-health
GET /analytics/safe-to-spend
```

## Goals

```text
GET    /goals
POST   /goals
GET    /goals/{id}
PATCH  /goals/{id}

POST   /goals/{id}/contributions
```

## Investments

```text
GET    /investments/portfolio
GET    /investments/holdings
POST   /investments/holdings
PATCH  /investments/holdings/{id}
DELETE /investments/holdings/{id}
```

## Settings

```text
GET   /settings/profile
PATCH /settings/profile

GET   /settings/preferences
PATCH /settings/preferences

GET    /settings/linked-providers
POST   /settings/linked-providers
DELETE /settings/linked-providers/{id}
```

---

# 125. APIs That Can Wait

The following should not block initial backend development:

```text
AI Insights
Direct bank integrations
Direct UPI synchronization
Advanced investment market synchronization
Push notifications
Household accounts
Multi-currency
Advanced report generation
Advanced recurring transactions
```

These should be introduced after the core transaction and analytics system is reliable.

---

# 126. Important V1 Principle

MoneyScope should solve the most important problem first:

> **"I use multiple UPI apps and at the end of the month I don't know where my money went."**

Therefore the backend priority is:

```text
Transaction ingestion
        ↓
Transaction normalization
        ↓
Unified transaction history
        ↓
Analytics
        ↓
Monthly financial understanding
        ↓
Budgeting
        ↓
Goals
        ↓
Investments
```

---

# 127. Final API Architecture

```text
                         MoneyScope PWA
                               │
                               │ REST / HTTPS
                               ▼
                         FastAPI /api/v1
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
          Auth             Finance           Insights
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        Accounts         Transactions       Investments
             │                │
             │          ┌─────┼──────┐
             │          ▼     ▼      ▼
             │       Budgets Goals Analytics
             │                       │
             └───────────────────────┤
                                     ▼
                              Financial Health
                                     │
                                     ▼
                                  Reports
```

---

# 128. Final API Principles

MoneyScope API follows these principles:

1. APIs are versioned.
2. Financial APIs require authentication.
3. User ownership is always verified server-side.
4. Financial calculations belong to the backend.
5. Money is represented using fixed precision.
6. Financial mutations should be transactional.
7. Important mutations support idempotency where required.
8. Collection endpoints support pagination.
9. Filtering and sorting are explicit and allow-listed.
10. Errors use machine-readable codes.
11. Frontend should not directly call external financial providers.
12. Frontend should not directly access the database.
13. TanStack Query manages server state.
14. FastAPI/OpenAPI provides the API contract.
15. The transaction system is the foundation for analytics and financial intelligence.

---

# 129. Document Status

**Status:** API Contract Approved for Backend Implementation

**Previous Document:**

`04_Database_Design.md`

**Next Document:**

`06_Backend_Architecture.md`

The next document should define the actual FastAPI project structure, modules, routers, services, repositories, SQLAlchemy models, Pydantic schemas, authentication flow, dependency injection, background workers, configuration, testing structure, and implementation conventions.
