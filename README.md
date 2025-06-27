# Credit Approval System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/) [![Django](https://img.shields.io/badge/Django-4.0%2B-green.svg)](https://www.djangoproject.com/) [![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)  
Project URL: [https://github.com/MOHIT-S-MAURYA/credit_approval_system](https://github.com/MOHIT-S-MAURYA/credit_approval_system)

A Django-based Credit Approval System for managing customers, loans, and eligibility using REST APIs and Excel data ingestion. Built for extensibility and easy deployment with Docker.

---

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Docker Setup](#docker-setup)
  - [Local Development](#local-development-without-docker)
- [Data Ingestion](#data-ingestion)
- [API Documentation](#api-documentation)
- [Management Commands](#management-commands)
- [Models](#models)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features
- Customer registration and management
- Loan creation, eligibility check, and management
- REST API with Django REST Framework
- Data ingestion from Excel files (`customer_data.xlsx`, `loan_data.xlsx`)
- PostgreSQL database support (via Docker)
- Admin dashboard for superusers
- Automated debt calculation and update

## Project Structure
```
credit_approval_system/
├── core/
│   ├── management/commands/   # Custom management commands
│   ├── migrations/
│   ├── models.py              # Django models (Customer, Loan)
│   ├── serializers.py         # DRF serializers
│   ├── utils.py               # Business logic utilities
│   ├── views.py               # API views
│   ├── urls.py                # API routes
│   └── ...
├── credit_approval_system/
│   ├── settings.py            # Django settings
│   └── ...
├── customer_data.xlsx         # Sample customer data
├── loan_data.xlsx             # Sample loan data
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- (For local development) Python 3.11+ and pip

### Docker Setup
1. **Clone the repository**
   ```sh
   git clone https://github.com/MOHIT-S-MAURYA/credit_approval_system.git
   cd credit_approval_system
   ```
2. **Start the services**
   ```sh
   docker-compose up --build
   ```
3. **Access the server**  
   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)
4. **Run management commands inside the container**
   ```sh
   docker exec -it credit_approval_system-web-1 bash
   ```

#### Superuser Credentials (Default)
- **Username:** admin
- **Password:** admin

### Local Development (without Docker)
1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Configure your database in `credit_approval_system/settings.py`.
3. Run migrations:
   ```sh
   python manage.py migrate
   ```
4. Create a superuser:
   ```sh
   python manage.py createsuperuser
   ```
5. Start the server:
   ```sh
   python manage.py runserver
   ```

## Data Ingestion
To load initial data from Excel files:
```sh
python manage.py load_excel_data
```
To update customer debt based on active loans:
```sh
python manage.py update_customer_debt
```
*Run these inside the running web container or your local environment.*

## API Documentation

### 1. Register Customer
- **POST** `/register`
- **Request Body:**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "phone_number": "1234567890",
    "monthly_income": 50000
  }
  ```
- **Response:**
  ```json
  {
    "customer_id": 1,
    "name": "John Doe",
    "age": 30,
    "monthly_income": 50000,
    "approved_limit": 1800000,
    "phone_number": "1234567890"
  }
  ```

### 2. Check Loan Eligibility
- **POST** `/check-eligibility`
- **Request Body:**
  ```json
  {
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 10.5,
    "tenure": 12
  }
  ```
- **Response:**
  ```json
  {
    "customer_id": 1,
    "approval": true,
    "interest_rate": 10.5,
    "corrected_interest_rate": 10.5,
    "tenure": 12,
    "monthly_installment": 8791.59
  }
  ```

### 3. View Loan Detail
- **GET** `/view-loan/<loan_id>/`
- **Response:**
  ```json
  {
    "loan_id": 1,
    "customer": {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "1234567890",
      "age": 30
    },
    "loan_amount": 100000,
    "interest_rate": 10.5,
    "monthly_installment": 8791.59,
    "tenure": 12
  }
  ```

### 4. View Loans by Customer
- **GET** `/view-loans/<customer_id>/`
- **Response:**
  ```json
  [
    {
      "loan_id": 1,
      "loan_amount": 100000,
      "interest_rate": 10.5,
      "monthly_installment": 8791.59,
      "repayments_left": 10
    },
    ...
  ]
  ```

### 5. Create Loan
- **POST** `/create-loan`
- **Request Body:**
  ```json
  {
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 10.5,
    "tenure": 12
  }
  ```
- **Response:**
  ```json
  {
    "loan_id": 2,
    "customer_id": 1,
    "loan_approved": true,
    "message": "Loan approved and created successfully.",
    "monthly_installment": 8791.59
  }
  ```

---

## Management Commands
- `python manage.py load_excel_data`  
  Ingests data from `customer_data.xlsx` and `loan_data.xlsx` into the database. Handles sequence resets for PostgreSQL.
- `python manage.py update_customer_debt`  
  Updates the `current_debt` field for each customer based on their active loans.

## Models

### Customer
- `customer_id` (AutoField, PK)
- `first_name` (CharField)
- `last_name` (CharField)
- `age` (PositiveIntegerField)
- `phone_number` (CharField, unique)
- `monthly_income` (DecimalField)
- `approved_limit` (DecimalField)
- `current_debt` (DecimalField)

### Loan
- `loan_id` (AutoField, PK)
- `customer` (ForeignKey to Customer)
- `loan_amount` (DecimalField)
- `interest_rate` (DecimalField)
- `tenure` (PositiveIntegerField, months)
- `monthly_payment` (DecimalField)
- `emi_paid_on_time` (PositiveIntegerField)
- `start_date` (DateField)
- `end_date` (DateField)

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License
This project is licensed under the MIT License.

## Contact
For questions or support, open an issue or contact [MOHIT-S-MAURYA](https://github.com/MOHIT-S-MAURYA).