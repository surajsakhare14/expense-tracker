# 02_Feature_Freeze_V1.md

# MoneyScope — Version 1 Feature Freeze

> **Version:** 1.0.0
>
> **Status:** Feature Freeze
>
> **Product:** MoneyScope
>
> **Purpose:** Define the exact scope of Version 1 and prevent uncontrolled feature expansion.

---

# 1. Purpose of This Document

This document defines the features that are officially included in MoneyScope Version 1.

The purpose of the feature freeze is to:

- Prevent feature creep
- Establish a clear development target
- Keep frontend and backend scope aligned
- Make database design predictable
- Make API design predictable
- Enable milestone-based development
- Ensure the team focuses on the core user problem

Once this document is approved, new features should NOT be added directly to V1.

New ideas should be evaluated and placed into the V1.1, V2, or Future Roadmap.

---

# 2. V1 Product Goal

MoneyScope V1 must allow a user to:

1. Record income
2. Track expenses
3. Manage financial accounts
4. Categorize transactions
5. Understand monthly spending
6. Set and track budgets
7. Create savings goals
8. Track investments
9. Understand financial health
10. View net worth
11. Review financial analytics
12. Generate a monthly financial report
13. Receive important financial notifications
14. Read a curated financial news feed

The primary outcome is:

> **A user should be able to understand their complete financial position from one application.**

---

# 3. V1 Scope Classification

Every feature belongs to one of these categories.

## P0 — Core / Must Have

The product cannot be considered functional without these features.

## P1 — Important

Strongly improves the V1 experience but depends on P0 functionality.

## P2 — Enhancement

Useful but can be implemented after the core system is stable.

## V2 — Future

Explicitly excluded from V1.

---

# 4. V1 Navigation

The final V1 application navigation is:

```text
Dashboard
Transactions
Analytics
Goals
Investments
Accounts
Reports
News
Settings
```

No additional primary navigation items should be added during V1 development without explicit approval.

---

# 5. Authentication & User Management

## Priority

P0 — Must Have

### Included

- User registration
- User login
- User logout
- Access token
- Refresh token
- Current user profile
- Basic profile information
- Password change
- Session expiration handling

### User Profile

User should have:

- Name
- Email
- Profile image/avatar (optional)
- Currency preference
- Timezone
- Created date

### Security

- Passwords must never be stored as plaintext
- Authenticated resources must be user-scoped
- Access tokens must expire
- Refresh token handling must be secure
- Sensitive operations should require authentication

### Excluded

- Social login
- OAuth provider login
- Multi-factor authentication

These can be added later.

---

# 6. Accounts

## Priority

P0 — Must Have

Accounts represent where the user's money exists or where financial activity originates.

### Supported Account Types

- Bank Account
- Cash
- Credit Card
- Wallet
- UPI-linked account
- Other

### Account Fields

Conceptually:

```text
Account

id
name
type
institution
current_balance
currency
status
created_at
updated_at
```

### Features

- Create account
- View accounts
- Edit account
- Archive account
- View account balance
- View account transactions
- Set account type
- Associate transactions with accounts

### UPI Provider

The account model should support provider information such as:

- Google Pay
- PhonePe
- Paytm
- Other UPI providers

Important:

> A UPI app is a payment channel/provider, not necessarily the underlying bank account.

The data model must preserve this distinction.

### Excluded

- Direct bank synchronization
- Automatic UPI synchronization
- Open banking integrations

---

# 7. Income

## Priority

P0 — Must Have

A personal finance application must understand both money coming in and money going out.

### Income Types

- Salary
- Freelance
- Business income
- Interest
- Dividend
- Cashback
- Refund
- Bonus
- Other

### Features

- Add income
- Edit income
- Delete/archive income
- Categorize income
- Assign income to account
- View income history
- Include income in analytics

### Dashboard

Income must contribute to:

- Monthly income
- Cash flow
- Savings
- Financial health
- Net worth calculations where applicable

---

# 8. Transactions

## Priority

P0 — Must Have

Transactions are the primary financial data source.

### Transaction Types

```text
Expense
Income
Transfer
Investment
Refund
```

The backend must distinguish transaction direction/type clearly.

### Core Features

- Add transaction
- Edit transaction
- Delete/archive transaction
- View transaction
- Search transactions
- Filter transactions
- Sort transactions
- Group transactions by date
- Filter by category
- Filter by account
- Filter by UPI provider
- Filter by transaction type
- Filter by date range

### Transaction Information

A transaction may contain:

```text
id
account
amount
type
merchant
category
description
occurred_at
payment_provider
source
reference
created_at
updated_at
```

### Merchant

Transactions should support merchant normalization.

Example:

```text
SWIGGY
Swiggy Pvt Ltd
SWIGGY ONLINE

↓

Swiggy
```

Full merchant normalization automation is not required in V1, but the data model should support it.

---

# 9. Transaction Import

## Priority

P0 — Must Have

Because users may use multiple UPI apps and banks, manual entry alone is insufficient.

### V1 Import Method

CSV import.

### Features

- Upload CSV
- Validate CSV
- Preview rows
- Map columns
- Validate transactions
- Detect duplicates
- Import valid transactions
- Report rejected rows
- Show import status

### Import Result

Example:

```text
Total Rows: 120

Imported: 112

Duplicates: 5

Rejected: 3
```

### Import History

The system should preserve import metadata.

Example:

```text
Import ID
File name
Source
Uploaded at
Total rows
Imported rows
Rejected rows
Status
```

### Excluded

- Automatic UPI synchronization
- Direct bank APIs
- SMS parsing
- Automatic notification parsing

These belong to future versions.

---

# 10. Categories

## Priority

P0 — Must Have

### Default Expense Categories

- Food
- Groceries
- Shopping
- Travel
- Transport
- Bills
- Entertainment
- Healthcare
- Education
- Personal Care
- Subscriptions
- Rent
- EMI
- Insurance
- Other

### Default Income Categories

- Salary
- Freelance
- Business
- Interest
- Dividend
- Cashback
- Refund
- Bonus
- Other

### Features

- Default categories
- User-created categories
- Rename categories
- Archive categories
- Assign category to transactions

### Future

Automatic AI categorization.

---

# 11. Dashboard

## Priority

P0 — Must Have

The dashboard is the user's financial command center.

### Required Components

## Financial Health

Display:

```text
Financial Health Score
```

Example:

```text
82 / 100
```

The score must eventually be explainable.

---

## Income Summary

Show:

```text
Monthly Income
Monthly Expense
Savings
Savings Rate
```

---

## Today's Spending

Show:

```text
Today's Spending
```

---

## Monthly Spending

Show:

```text
This Month
Compared with Previous Month
```

---

## Net Worth

Show:

```text
Assets
Liabilities
Net Worth
```

---

## Safe-to-Spend

Show an estimated:

```text
Safe to Spend Today
```

The calculation should consider configured budgets and known upcoming obligations.

It must be clearly labeled as an estimate.

---

## Spending Trend

Show:

- Daily spending
- Monthly trend
- Previous-period comparison

---

## Category Breakdown

Show:

- Top spending categories
- Amount
- Percentage

---

## Goals Preview

Show:

- Goal name
- Saved amount
- Target amount
- Progress

---

## Investment Summary

Show:

- Invested amount
- Current value
- Return

---

## Recent Transactions

Show latest transactions.

---

## Alerts

Show important financial notifications.

---

# 12. Analytics

## Priority

P1 — Important

Analytics should answer financial questions rather than simply display charts.

### Required Analytics

## Spending Trend

- Daily
- Weekly
- Monthly

---

## Category Analysis

Show:

- Amount
- Percentage
- Trend

---

## Merchant Analysis

Show:

- Total spending
- Transaction count
- Average transaction

---

## UPI Provider Analysis

Show spending by provider.

Example:

```text
PhonePe
Google Pay
Paytm
Other
```

---

## Income vs Expense

Show:

```text
Income
Expense
Savings
```

---

## Monthly Comparison

Compare:

```text
Current Month
Previous Month
```

---

## Budget Utilization

Show:

```text
Budget
Spent
Remaining
Utilization
```

---

## Analytics Rules

Analytics should be calculated by the backend.

The frontend should not calculate financial totals from large transaction datasets.

---

# 13. Budgets

## Priority

P1 — Important

### Budget Types

V1 should support:

- Overall monthly budget
- Category budgets

Example:

```text
Monthly Budget
₹30,000

Food
₹5,000

Shopping
₹4,000

Travel
₹3,000
```

### Features

- Create budget
- Edit budget
- Archive budget
- View utilization
- View remaining budget
- Budget alerts

### Alert Thresholds

Default thresholds may include:

```text
70% — Informational
80% — Warning
90% — High Warning
100% — Exceeded
```

Thresholds should be configurable later.

---

# 14. Goals

## Priority

P1 — Important

### Features

- Create goal
- Edit goal
- Archive goal
- Set target amount
- Set deadline
- Add contribution
- View progress
- View remaining amount
- Mark completed

### Example

```text
Emergency Fund

Target
₹1,50,000

Saved
₹92,000

Progress
61%

Deadline
December 2026
```

### Goal Types

Optional predefined types:

- Emergency Fund
- Travel
- Education
- Vehicle
- Home
- Large Purchase
- Custom

---

# 15. Investments

## Priority

P1 — Important

V1 investment functionality focuses on tracking and visibility.

It does NOT provide trading functionality.

### Supported Asset Types

Initial support:

- Mutual Funds
- Stocks
- Fixed Deposits
- Gold
- Other investments

### Features

- Add holding
- Edit holding
- Archive holding
- Track invested amount
- Track current value
- Calculate profit/loss
- Calculate return percentage
- View allocation
- View portfolio summary
- View historical portfolio trend where data is available

### Excluded

- Buying investments
- Selling investments
- Trading
- Automated SIP execution
- Broker API integration
- Live market execution

---

# 16. Financial Health

## Priority

P1 — Important

Financial Health is a major MoneyScope feature.

### Initial Factors

The score may consider:

- Savings rate
- Budget adherence
- Goal progress
- Investment consistency
- Emergency fund progress
- Debt obligations
- Spending behavior

### Requirements

The score must:

- Be explainable
- Show contributing factors
- Show areas for improvement
- Avoid misleading users

Example:

```text
Financial Health

82 / 100

Savings       Good
Budget        Excellent
Goals         Good
Investments   Good
Emergency     Needs Improvement
```

The exact scoring algorithm will be defined separately before implementation.

---

# 17. Net Worth

## Priority

P1 — Important

Net worth:

```text
Assets - Liabilities
```

### Assets

- Bank accounts
- Cash
- Investments
- Wallet balances

### Liabilities

- Credit card balances
- Loans
- Other liabilities

### Features

- Current net worth
- Net worth history
- Asset breakdown
- Liability breakdown

---

# 18. Reports

## Priority

P1 — Important

### Monthly Financial Report

The report should include:

```text
Income
Expenses
Savings
Savings Rate
Top Category
Top Merchant
Budget Performance
Goals Progress
Investment Summary
Financial Health
Net Worth
```

### Features

- Generate report
- View report
- Select month
- Download PDF

### Future

- Share report
- Automated monthly email
- AI-generated summary

---

# 19. Notifications

## Priority

P1 — Important

### Notification Types

- Budget warning
- Budget exceeded
- Goal milestone
- Goal completed
- Bill reminder
- Monthly report available
- Financial insight

### Notification Center

Users should be able to:

- View notifications
- Mark as read
- Delete/archive notification

### Future

- Push notifications
- Email notifications
- Smart notification timing

---

# 20. News

## Priority

P2 — Enhancement

Financial news is important to the product vision but is not part of the core financial data system.

### Categories

- Personal Finance
- RBI
- Tax
- Mutual Funds
- Markets
- Economy
- Insurance
- Savings
- Investments

### Features

- View news
- Category filter
- Featured/hot news
- Article details
- External article link

### V1 Requirement

News should be curated and cached.

The system should not depend on live external news APIs for every page request.

---

# 21. Settings

## Priority

P0/P1

### Profile

- Name
- Email
- Avatar

### Preferences

- Theme
- Currency
- Timezone
- Notification preferences

### Security

- Change password
- Logout
- Session management

### Account Preferences

- Default account
- Default category

### Excluded

- Advanced role management
- Organization settings
- Family account management

---

# 22. PWA Requirements

## Priority

P1

MoneyScope must remain installable as a Progressive Web App.

### V1 Requirements

- Installable
- Responsive
- Mobile-first
- App manifest
- App icons
- Service worker
- Offline shell
- Fast loading
- Appropriate loading states

### Offline Scope

V1 offline functionality should focus on:

- Loading previously cached UI
- Viewing cached information where safe

Financial mutations should not silently succeed offline.

Any offline transaction creation must have an explicit synchronization strategy before being enabled.

---

# 23. Data Import & Data Ownership

Users must be able to understand where imported data came from.

Each transaction should have a source such as:

```text
manual
csv
bank_import
upi_import
api
```

V1 primarily supports:

```text
manual
csv
```

The architecture should allow future sources.

---

# 24. Search & Filtering

## Priority

P0/P1

Transactions must support:

- Search by merchant
- Category filter
- Account filter
- UPI provider filter
- Date filter
- Transaction type
- Amount range
- Sort order

Analytics should support appropriate date/period filters.

---

# 25. Loading, Empty & Error States

Every V1 screen must support three states.

## Loading

Use:

- Skeletons
- Loading indicators
- Disabled mutation buttons

---

## Empty

Examples:

```text
No transactions yet.

Add your first transaction.
```

```text
No goals yet.

Create your first financial goal.
```

---

## Error

Errors must be:

- Human-readable
- Actionable
- Non-technical

Example:

```text
We couldn't load your transactions.

Please try again.
```

Technical details should be logged but not exposed to users.

---

# 26. Accessibility

V1 should support:

- Keyboard navigation
- Semantic HTML
- Accessible labels
- Screen-reader-friendly controls
- Sufficient contrast
- Focus states
- Accessible dialogs
- Accessible charts where practical

---

# 27. Responsive Design

MoneyScope is mobile-first.

The following must work correctly on:

- Mobile
- Tablet
- Desktop

Priority should be:

```text
Mobile
↓
Tablet
↓
Desktop
```

The primary financial workflows should remain usable on small screens.

---

# 28. V1 Explicitly Excluded Features

The following features are NOT part of V1.

## Financial Integrations

- Direct bank synchronization
- Automatic UPI synchronization
- Account Aggregator integration
- SMS transaction parsing
- Notification scraping
- Broker integrations

---

## AI

- AI chatbot
- AI financial advisor
- Voice assistant
- AI-generated investment recommendations
- AI stock predictions
- AI trading

Rule-based financial insights may be implemented where required for V1.

---

## Documents

- Receipt OCR
- Invoice OCR
- Automatic receipt scanning

---

## Social / Family

- Family accounts
- Shared budgets
- Shared wallets
- Expense splitting
- Social finance

---

## Lending

- Loans
- EMI management beyond basic transaction tracking
- Credit score
- Credit recommendations

---

## Tax

- Tax filing
- Automated ITR
- Tax optimization

---

## Trading

- Buy/sell investments
- Broker execution
- Automated trading
- Portfolio rebalancing execution

---

# 29. V1 Feature Matrix

| Module           | Priority | V1 |
| ---------------- | -------- | -- |
| Authentication   | P0       | ✅  |
| User Profile     | P0       | ✅  |
| Accounts         | P0       | ✅  |
| Income           | P0       | ✅  |
| Transactions     | P0       | ✅  |
| Categories       | P0       | ✅  |
| CSV Import       | P0       | ✅  |
| Dashboard        | P0       | ✅  |
| Budgets          | P1       | ✅  |
| Goals            | P1       | ✅  |
| Analytics        | P1       | ✅  |
| Financial Health | P1       | ✅  |
| Net Worth        | P1       | ✅  |
| Investments      | P1       | ✅  |
| Reports          | P1       | ✅  |
| Notifications    | P1       | ✅  |
| News             | P2       | ✅  |
| Settings         | P0/P1    | ✅  |
| PWA              | P1       | ✅  |
| Bank Sync        | V2       | ❌  |
| UPI Auto Sync    | V2       | ❌  |
| AI Assistant     | V2       | ❌  |
| OCR              | V2       | ❌  |
| Family Accounts  | V2       | ❌  |
| Tax Filing       | V2       | ❌  |
| Credit Score     | V2       | ❌  |
| Trading          | V2       | ❌  |

---

# 30. V1 Development Priority

The feature priority does NOT determine implementation order.

Implementation should follow domain dependencies.

Recommended order:

```text
Authentication
      ↓
Users
      ↓
Accounts
      ↓
Categories
      ↓
Transactions
      ↓
Budgets
      ↓
Goals
      ↓
Investments
      ↓
Dashboard
      ↓
Analytics
      ↓
Financial Health
      ↓
Net Worth
      ↓
Reports
      ↓
Notifications
      ↓
News
```

---

# 31. V1 Completion Criteria

MoneyScope V1 is considered feature-complete when:

## Authentication

- Users can register
- Users can login
- Users can logout
- Protected resources work correctly

## Accounts

- Users can create and manage accounts
- Transactions can be associated with accounts

## Transactions

- Users can create transactions
- Users can edit transactions
- Users can delete/archive transactions
- Users can search and filter transactions
- Users can import CSV data

## Income

- Users can record income
- Income appears in cash-flow calculations

## Budgets

- Users can create budgets
- Users can monitor utilization
- Budget alerts work

## Goals

- Users can create goals
- Users can add contributions
- Progress updates correctly

## Investments

- Users can track holdings
- Portfolio totals calculate correctly

## Dashboard

- All key metrics come from backend data
- No production dashboard metrics depend on hard-coded mock data

## Analytics

- Charts use backend-derived data
- Monthly comparisons work
- Category and provider analysis work

## Reports

- Monthly reports can be generated
- PDF export works

## Notifications

- Important financial events generate notifications

## News

- News feed loads correctly
- Categories work
- External articles open safely

## PWA

- App is installable
- Mobile experience works
- Offline shell works

---

# 32. Frontend Feature Freeze Rule

The current Lovable frontend is considered the V1 visual baseline.

After this document is approved:

### Allowed

- Bug fixes
- Accessibility improvements
- Responsive fixes
- Backend integration
- Loading states
- Empty states
- Error states
- Small UI adjustments required by real data

### Not Allowed Without Review

- New primary navigation pages
- Major redesigns
- New financial domains
- New product concepts
- Major component rewrites
- New third-party integrations

Any new feature must first be added to the product roadmap.

---

# 33. Backend Feature Freeze Rule

Backend development must follow the approved V1 domains.

Do not introduce unrelated domains during implementation.

For example:

```text
Good:

Transaction → Merchant normalization

Bad:

Transaction → AI chatbot
```

The second belongs to a future roadmap.

---

# 34. Definition of Done

A feature is not considered complete simply because the API or UI works.

Every V1 feature should include:

```text
Requirements
    ↓
Database
    ↓
API
    ↓
Validation
    ↓
Business Logic
    ↓
Frontend Integration
    ↓
Loading State
    ↓
Empty State
    ↓
Error Handling
    ↓
Tests
    ↓
Documentation
```

Only then is the feature considered complete.

---

# 35. Feature Change Process

If a new feature is proposed during V1 development:

## Step 1

Document the feature.

## Step 2

Explain the user problem it solves.

## Step 3

Estimate technical complexity.

## Step 4

Identify affected modules.

## Step 5

Determine whether it is critical for V1.

## Step 6

If not critical, move it to V2.

## Step 7

If critical, update this document before implementation.

No feature should enter development simply because it is technically interesting.

---

# 36. V1 Product Boundary

MoneyScope V1 focuses on:

```text
TRACK
  ↓
UNDERSTAND
  ↓
CONTROL
  ↓
PLAN
  ↓
GROW
```

It does NOT attempt to become:

```text
Bank
Broker
Lender
Tax Filing Platform
AI Financial Advisor
Payment App
```

Those are future possibilities, not V1 responsibilities.

---

# 37. Final V1 Statement

MoneyScope V1 is a complete personal finance management platform focused on helping users understand their income, expenses, accounts, budgets, goals, investments, and financial health.

The V1 objective is not to build every possible financial feature.

The objective is to build a reliable foundation that users can trust with their financial data.

> **Build the financial foundation first. Intelligence and automation come later.**

---


### 🔒 What this means for us

After this document is approved, **we should consider the frontend feature scope frozen**.

The important part is that I added a few things that weren't explicit enough before:

- **Income is P0**, because without it cash flow is incomplete.
- **Accounts are P0**, because transactions need an actual financial source.
- **Transfers are explicitly modeled**, so moving ₹10,000 from HDFC to ICICI doesn't become a fake ₹10,000 expense.
- **CSV import is P0**, because your multiple-UPI problem needs a practical V1 solution without waiting for bank/UPI integrations.
- **Budgets are P1**, but they are required for the "Safe to Spend" and financial-health experience.
- **AI is deliberately V2**; we can still have deterministic/rule-based insights in V1.
- **Bank/UPI automatic sync is V2**, which keeps the first release achievable.
- **Loading/empty/error states are part of V1**, not "polish for later."
- **PWA offline mutations are not enabled casually**—financial data synchronization needs a proper conflict strategy first.

One particularly important architectural decision is **transaction types**: `expense`, `income`, `transfer`, `investment`, and `refund`. That will prevent some nasty accounting bugs later.

**Next:** `03_System_Architecture.md` should turn this product scope into the actual architecture: **Lovable/TanStack frontend → FastAPI → service/domain layer → repositories → PostgreSQL**, plus Redis, authentication, background jobs, file imports, and deployment.