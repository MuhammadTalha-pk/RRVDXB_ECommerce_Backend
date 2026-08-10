=======
# RRVDXB E-Commerce Backend

Backend API for the **RRVDXB E-Commerce Platform**.

Built with **FastAPI** and **PostgreSQL**.

## Technologies

- Python
- FastAPI
- PostgreSQL
- JWT Authentication
- bcrypt
- Stripe API
- OpenAI API
- SendGrid / SMTP

## Main Features

- User registration and login
- JWT authentication
- Product management
- Category and brand management
- Shopping cart
- Orders and order tracking
- Wallet system
- Stripe payments
- Admin management
- AI shopping features
- Swagger API documentation

## AI Features

- AI Shopping Chatbot
- Product Recommender
- Price Predictor
- Deal Finder
- Trend Analyzer
- Review Sentiment Analysis

## Project Structure

```text
app/
├── main.py
├── core/
├── models/
├── schemas/
├── api/
├── services/
├── ai/
├── middleware/
└── utils/

requirements.txt
.env
README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/MuhammadTalha-pk/RRVDXB_ECommerce_Backend.git
cd RRVDXB_ECommerce_Backend
```

Create virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file and add your required settings for:

```env
DATABASE_URL=
JWT_SECRET_KEY=
STRIPE_SECRET_KEY=
OPENAI_API_KEY=
SENDGRID_API_KEY=
```

## Run the Project

```bash
uvicorn app.main:app --reload
```

API will run at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Main API Modules

- Authentication
- Users
- Products
- Categories
- Brands
- Cart
- Orders
- Wallet
- Payments
- AI
- Admin

## Backend Team

**Muhammad Talha**  
AI + Backend Lead

**Faisal Majeed**  
AI + Backend Developer

## Project

**RRVDXB - Premium E-Commerce Platform**

Developed for **TechNexus Virtual University**.
