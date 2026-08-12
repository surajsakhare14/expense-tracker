# 00_Project_Context.md

# MoneyScope - Project Context

> **Version:** 1.0.0
>
> **Status:** Planning & Architecture
>
> **Project Type:** Personal Finance Platform (PWA)
>
> **Owner:** Suraj Sakhare

---

# Overview

MoneyScope is a modern, API-first Personal Finance Operating System (PFOS) designed to help users understand, manage, and grow their financial life from a single application.

Unlike traditional expense trackers that only record transactions, MoneyScope provides a complete financial dashboard combining:

- Income Tracking
- Expense Management
- Budget Planning
- Financial Goals
- Investments
- Financial Analytics
- Monthly Reports
- Financial News
- Smart Financial Insights

The application follows a production-grade architecture inspired by modern fintech products such as:

- CRED
- Jupiter
- INDmoney
- Groww
- Walnut
- Money Manager

The long-term vision is to become a complete financial companion for everyday users.

---

# Problem Statement

Most users manage money across multiple platforms:

- Google Pay
- PhonePe
- Paytm
- Bank Accounts
- Credit Cards
- Cash
- Wallets

As a result:

- Spending becomes difficult to track.
- Monthly expenses are unclear.
- Savings are inconsistent.
- Financial goals are forgotten.
- Investments are scattered.
- Users rarely understand where their money actually goes.

Most expense tracking applications focus only on recording transactions rather than helping users make better financial decisions.

MoneyScope aims to solve this problem.

---

# Vision

Enable users to understand every rupee they earn, spend, save, and invest through one intelligent financial platform.

MoneyScope should become the user's daily financial dashboard rather than simply another expense tracker.

---

# Mission

Help users:

- Understand spending habits
- Build better financial discipline
- Achieve financial goals
- Increase savings
- Track investments
- Improve financial health
- Make informed financial decisions

---

# Target Audience

Primary Users

- Salaried professionals
- Young professionals
- Students
- Freelancers
- Software engineers
- Small business owners

Initial MVP focuses on:

Indian salaried professionals using UPI for daily payments.

---

# Product Principles

MoneyScope follows these principles.

## 1. Simplicity

The application should remain easy to understand.

Avoid unnecessary complexity.

Every screen should answer one important financial question.

---

## 2. User-Centric

Every feature must solve a real financial problem.

Avoid adding features because they are technically interesting.

---

## 3. Data First

The application should rely on structured financial data.

Dashboards and analytics should be generated from backend data rather than frontend calculations.

---

## 4. API First

Frontend and backend remain independent.

Frontend communicates only through REST APIs.

The frontend should never directly access the database.

---

## 5. Modular Architecture

Each business domain should remain independent.

Examples:

- Users
- Accounts
- Transactions
- Budgets
- Goals
- Investments
- Reports

Every module should own its:

- Models
- Schemas
- Services
- Repository
- APIs
- Tests

---

## 6. Scalability

The architecture should support future features without major redesign.

Future features include:

- Bank integrations
- UPI integrations
- AI insights
- OCR receipt scanning
- Subscription detection
- Financial forecasting

---

# Current Project Status

Current frontend has been completed using Lovable AI.

Current state:

- Modern UI
- Responsive Design
- Dashboard
- Analytics
- Transactions
- Goals
- Investments
- News
- Settings

The frontend currently uses mock financial data.

Backend development has not started.

The backend will gradually replace all mock data using REST APIs.

---

# Technology Stack

## Frontend

- React 19
- TanStack Start
- TanStack Router
- TanStack Query
- TypeScript
- Tailwind CSS v4
- shadcn/ui
- Radix UI
- Recharts
- React Hook Form
- Zod
- Lucide Icons
- Vite

---

## Backend

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- JWT Authentication
- Pydantic v2
- Pytest

---

## Infrastructure

Frontend

- Vercel

Backend

- Railway / Render

Database

- Neon PostgreSQL

Object Storage

- Cloudflare R2 / AWS S3

---

# Development Philosophy

The project follows professional software engineering practices.

Development order:

Problem
↓

Product Design
↓

Architecture
↓

Database Design
↓

API Contracts
↓

Backend Development
↓

Frontend Integration
↓

Testing
↓

Deployment

Code should never be written before architecture is finalized.

---

# Architecture Philosophy

The project follows:

- API First
- Feature-Based Architecture
- Clean Architecture
- Separation of Concerns
- Domain-Oriented Modules

The backend is organized around business domains instead of pages.

Example:

Users

↓

Accounts

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

Reports

↓

Notifications

---

# Coding Standards

General principles:

- Keep code simple.
- Prefer readability over cleverness.
- Avoid duplicated logic.
- Write reusable components.
- Follow SOLID principles where appropriate.
- Keep business logic outside route handlers.
- Keep UI independent from backend implementation.

---

# Design Philosophy

UI should feel premium but simple.

Design goals:

- Mobile First
- Responsive
- Accessible
- Fast
- Clean
- Professional

The design language should resemble modern fintech products rather than enterprise dashboards.

---

# Security Principles

Security is considered from day one.

Planned security measures include:

- JWT Authentication
- Password hashing
- Role-based permissions (future)
- Input validation
- SQL injection prevention
- Rate limiting
- Audit logs
- Secure environment variables
- HTTPS only
- Secure HTTP headers

---

# Long-Term Vision

Future roadmap includes:

- Live Bank Integrations
- UPI Sync
- OCR Bill Scanner
- AI Financial Assistant
- Smart Budget Recommendations
- Subscription Detection
- Investment Portfolio Sync
- Tax Insights
- Financial Health Score
- Monthly AI Reports

These features are intentionally outside the initial MVP.

---

# AI Development Guidelines

AI tools (GitHub Copilot, ChatGPT, Claude) should follow these rules when contributing:

- Understand the existing architecture before suggesting changes.
- Do not introduce breaking changes without justification.
- Prefer reusable and maintainable solutions.
- Do not duplicate business logic.
- Follow the documented folder structure.
- Keep frontend and backend loosely coupled.
- Generate production-ready code.
- Write meaningful tests when adding new functionality.
- Explain architectural trade-offs when recommending changes.

---

# Definition of Success

MoneyScope Version 1 is successful when users can:

- Record income and expenses
- Manage accounts
- Track budgets
- Monitor financial goals
- View analytics
- Generate monthly reports
- Understand financial health
- Access all financial information from one dashboard

without relying on multiple applications.

---

# Document Ownership

This document serves as the foundational reference for the project.

All future architectural, product, and development decisions should align with the principles defined here.

Major changes to this document should be carefully reviewed, as they may impact the overall direction of the project.