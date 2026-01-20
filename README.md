# E-Commerce Web Application

A full-stack e-commerce web application built with Django, featuring product management,
shopping cart, secure checkout, and multiple payment gateway integrations.
The system is deployed on AWS EC2 and supports social authentication and cloud-hosted databases.

---

## Features
- User authentication with Google and Facebook OAuth
- Product browsing and detailed product pages
- Add-to-cart and cart management
- Secure checkout process
- Online payments via VNPay and PayPal (Sandbox)
- Order creation and payment status tracking
- Admin dashboard for product and order management
- Cloud-hosted database with SSL-secured connection

---

## Tech Stack

### Backend
- Django – core backend framework
- Django REST Framework – API development
- Python – business logic and payment integration

### Frontend
- HTML5 – page structure
- CSS3 – layout and styling
- JavaScript (ES6) – client-side interactions

### Database
- MySQL – cloud-hosted relational database (Aiven)

### Authentication
- Google OAuth 2.0
- Facebook Login

### Payment Gateways
- VNPay – domestic payment gateway integration
- PayPal – international payment gateway integration

### Deployment & Infrastructure
- AWS EC2 (Ubuntu) – application hosting
- Nginx – reverse proxy and static file serving
- Gunicorn – WSGI application server
- DuckDNS – domain name mapping for public access

### Tools
- Git & GitHub – version control

---

## Architecture
- Django MVT architecture
- RESTful API design
- Secure payment workflow
- Separation of frontend, backend, and database layers

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- Aiven MySQL service (or any cloud MySQL provider)
- VNPay sandbox account
- PayPal sandbox account
- Google & Facebook OAuth credentials



### Environment Variables
Create a `.env` file in the project root:

```env
SECRET_KEY=your_django_secret_key

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port

VN_PAY_TMN_CODE=your_vnpay_code
VN_PAY_HASH_SECRET=your_vnpay_secret

PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret

GOOGLE_CLIENT_ID=your_google_client_id
FACEBOOK_CLIENT_ID=your_facebook_client_id
