# credit_approval_system

A Django-based Credit Approval System.

## Features

- Customer and loan management
- REST API with Django REST Framework
- Data ingestion from Excel files
- PostgreSQL database support (via Docker)

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- (For local development) Python 3.11+ and pip

### Setup & Run (Docker)

1. **Clone the repository**  
   ```sh
   git clone <repo-url>
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

### Superuser Credentials

- **Username:** admin  
- **Password:** admin

### Data Ingestion

To load initial data from Excel files:
```sh
python manage.py load_excel_data
```
*(Run this inside the running web container or your local environment.)*

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

## Project Structure

```
credit_approval_system/
├── core/
│   ├── management/commands/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   └── ...
├── credit_approval_system/
│   ├── settings.py
│   └── ...
├── customer_data.xlsx
├── loan_data.xlsx
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```