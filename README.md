RRVDXB E-Commerce Backend

<p align="center">
  <strong>FastAPI + PostgreSQL backend for RRVDXB, a premium AI-powered e-commerce platform.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/JWT-Authentication-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT">
  <img src="https://img.shields.io/badge/Stripe-Payments-635BFF?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe">
  <img src="https://img.shields.io/badge/OpenAI-AI-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI">
</p>

Overview

RRVDXB is a premium full-stack e-commerce platform designed for customers in the UAE, KSA, Pakistan, and UK.

This repository contains the Python FastAPI backend responsible for authentication, product management, shopping cart operations, orders, wallets, payments, admin functionality, and AI-powered shopping services.

Backend Responsibilities

JWT-based user authentication

User management

Product, category, and brand APIs

Shopping cart management

Order creation, history, status updates, and tracking

Digital wallet and transaction management

Stripe payment integration

AI shopping APIs

Admin operations

PostgreSQL persistence

Rate limiting and CORS

Centralized error handling

Email integration

Swagger/OpenAPI documentation

Tech Stack

Layer

Technology

Backend

Python + FastAPI

Database

PostgreSQL

Authentication

JWT + bcrypt

AI/ML

OpenAI API + LangChain

Payments

Stripe API

Email

SendGrid / SMTP

API Docs

Swagger / OpenAPI

Deployment

Render

Core Features

Authentication

Register users

Login users

JWT access/refresh flow

Logout

Password hashing with bcrypt

Protected routes

Products

Product CRUD

Categories

Brands

Search

Filter products by category

Filter products by brand

Featured and best-selling products

Inventory/stock support

Shopping Cart

Add products

Update quantity

Remove items

Clear cart

Cart summary support

Orders

Create orders

View order history

View order details

Track orders

Admin order status updates

Wallet

Wallet balance

Add money

Transaction history

Wallet-based checkout support

Payments

Stripe-based online payments

Admin

Product management

Category management

Brand management

Order management

User management

Wallet management

Coupon management

AI Services

AI Shopping Chatbot

Product Recommender

Price Predictor

Deal Finder

Trend Analyzer

Review Sentiment Analyzer

AI Capabilities

The backend is designed to expose AI-powered shopping features through FastAPI.

AI Feature

Purpose

Shopping Chatbot

Product recommendations, shopping advice, deal alerts, comparisons, and order assistance

Product Recommender

Personalized suggestions and “customers also bought” recommendations

Price Predictor

Predicts possible price drops and helps identify a better time to buy

Deal Finder

Finds discounts and promotional opportunities

Trend Analyzer

Analyzes shopping trends

Review Sentiment

Analyzes sentiment in product reviews

API Endpoints

The following endpoints are defined in the supplied project specification.

Authentication

Method

Endpoint

Access

Description

POST

/api/auth/register

Public

Register a user

POST

/api/auth/login

Public

Login

POST

/api/auth/refresh

Private

Refresh token

POST

/api/auth/logout

Private

Logout

Products

Method

Endpoint

Access

Description

GET

/api/products

Public

Get all products

GET

/api/products/{id}

Public

Get product details

GET

/api/products/category/{id}

Public

Get products by category

GET

/api/products/brand/{id}

Public

Get products by brand

GET

/api/products/search?q=

Public

Search products

POST

/api/products

Admin

Create product

PUT

/api/products/{id}

Admin

Update product

DELETE

/api/products/{id}

Admin

Delete product

Cart

Method

Endpoint

Access

Description

GET

/api/cart

Private

Get cart

POST

/api/cart/add

Private

Add item

PUT

/api/cart/update/{id}

Private

Update quantity

DELETE

/api/cart/remove/{id}

Private

Remove item

DELETE

/api/cart/clear

Private

Clear cart

Orders

Method

Endpoint

Access

Description

POST

/api/orders

Private

Create order

GET

/api/orders

Private

Get user orders

GET

/api/orders/{id}

Private

Get order details

GET

/api/orders/{id}/track

Private

Track order

PUT

/api/orders/{id}/status

Admin

Update order status

Wallet

Method

Endpoint

Access

Description

GET

/api/wallet

Private

Get wallet

POST

/api/wallet/add

Private

Add money

GET

/api/wallet/transactions

Private

Get transaction history

AI

Method

Endpoint

Access

Description

POST

/api/ai/chat

Private

AI shopping chatbot

GET

/api/ai/recommendations

Private

Product recommendations

POST

/api/ai/price-predict

Private

Price prediction

GET

/api/ai/deals

Public

Best deals

GET

/api/ai/trends

Public

Shopping trends

POST

/api/ai/sentiment

Admin

Review sentiment analysis

Additional backend modules include users, categories, brands, payments, and admin functionality. Their exact URL mappings should follow the router implementation in app/api/v1/.

Database

The project specification defines a PostgreSQL database with 12 main tables:

users

categories

brands

products

cart

orders

wallets

wallet_transactions

reviews

wishlist

chat_history

coupons

Key relationships connect users with carts, orders, wallets, reviews, wishlists, and chat history, while products reference categories and brands.

Project Structure

rrvdxb-backend/
│
├── app/
│   ├── main.py
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── dependencies.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── category.py
│   │   ├── brand.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   ├── wallet.py
│   │   ├── review.py
│   │   └── chat.py
│   │
│   ├── schemas/
│   │   ├── user_schema.py
│   │   ├── product_schema.py
│   │   ├── order_schema.py
│   │   └── wallet_schema.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── users.py
│   │       │   ├── products.py
│   │       │   ├── categories.py
│   │       │   ├── brands.py
│   │       │   ├── cart.py
│   │       │   ├── orders.py
│   │       │   ├── wallets.py
│   │       │   ├── payments.py
│   │       │   ├── ai.py
│   │       │   └── admin.py
│   │       └── router.py
│   │
│   ├── services/
│   │   ├── email_service.py
│   │   ├── payment_service.py
│   │   └── ai_service.py
│   │
│   ├── ai/
│   │   ├── chatbot.py
│   │   ├── recommender.py
│   │   ├── price_predictor.py
│   │   ├── deal_finder.py
│   │   ├── trend_analyzer.py
│   │   └── sentiment_analyzer.py
│   │
│   ├── middleware/
│   │   ├── cors.py
│   │   ├── rate_limit.py
│   │   └── error_handler.py
│   │
│   └── utils/
│       ├── constants.py
│       ├── helpers.py
│       └── validators.py
│
├── .env
├── requirements.txt
└── README.md

Getting Started

1. Clone the Repository

git clone https://github.com/MuhammadTalha-pk/RRVDXB_ECommerce_Backend.git
cd RRVDXB_ECommerce_Backend

2. Create a Virtual Environment

Windows

python -m venv venv
venv\Scripts\activate

macOS / Linux

python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables

Create a .env file in the project root.

The project documentation requires configuration for PostgreSQL, JWT authentication, Stripe, OpenAI, and SendGrid/SMTP.

A typical configuration may look like:

DATABASE_URL=postgresql://username:password@localhost:5432/rrvdxb

JWT_SECRET_KEY=replace_with_a_secure_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

STRIPE_SECRET_KEY=your_stripe_secret_key

OPENAI_API_KEY=your_openai_api_key

SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=your_email@example.com

Important: The supplied documentation identifies the required services but does not define the exact environment-variable names. Match these names with the settings expected in app/core/config.py.

5. Create the PostgreSQL Database

Create a PostgreSQL database and set its connection URL in .env.

Example:

CREATE DATABASE rrvdxb;

Apply the project migrations/schema before starting the application.

6. Run the Development Server

uvicorn app.main:app --reload

The API will normally be available at:

http://127.0.0.1:8000

API Documentation

FastAPI automatically provides interactive API documentation.

Swagger UI

http://127.0.0.1:8000/docs

ReDoc

http://127.0.0.1:8000/redoc

Use Swagger UI or Postman to test protected and public endpoints.

Authentication

Protected endpoints use JWT authentication.

Typical request header:

Authorization: Bearer <access_token>

Passwords are stored using bcrypt hashing.

Security & Middleware

The backend specification includes:

JWT authentication

bcrypt password hashing

CORS configuration

API rate limiting

Centralized error handling

Environment-based secret management

HTTP status-code based API errors

Never commit your .env file or production credentials.

Recommended .gitignore entries:

.env
venv/
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.idea/
.vscode/

Deployment

The backend is intended to be deployed on Render.

A typical production start command for FastAPI is:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Before deployment, verify:

PostgreSQL connection is configured

Environment variables are added in Render

JWT authentication works

CORS is configured for the frontend domain

Rate limiting is enabled

Email service is configured

Stripe keys are configured

AI API keys are configured

Swagger docs are accessible at /docs

All endpoints are tested

Backend Checklist

All API endpoints tested with Postman

Swagger documentation accessible at /docs

PostgreSQL schema/migrations applied

JWT authentication working

Rate limiting configured

CORS properly configured

Error handling returns appropriate status codes

Email service working

Stripe integration configured

AI services configured

Environment variables secured

Backend deployed on Render

Contributors

Backend Team

Muhammad TalhaAI + Backend Lead — FastAPI setup, PostgreSQL schema, authentication, core APIs, Stripe integration, AI Trend Analyzer, and backend deployment.

Faisal MajeedAI + Backend — AI Review Sentiment, AI API integrations, CORS, rate limiting, error handling, email service, and file upload.

AI Integration Team

Ameema Rashid — AI Shopping Chatbot

Saad Aziz — AI Price Predictor

Ubaid Ullah Farooqui — AI Product Recommender

Hira Abdullah — AI Deal Finder

Project

RRVDXB — Premium E-Commerce Platform

Built as a full-stack Web + AI e-commerce project for TechNexus Virtual University.

<p align="center">
  <strong>RRVDXB Backend — Fast, secure, scalable, and AI-powered.</strong>
</p>
