#!/bin/sh
set -e
# entrypoint.sh
echo "Starting Django application..."

# Wait for the database to be ready
echo "Waiting for database to be ready..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "Database is ready."

echo "Applying migrations..."
python manage.py migrate

echo "Loading Excel data..."
python manage.py load_excel_data

echo "Updating customer debt..."
python manage.py update_customer_debt


echo "Creating superuser (if not exists)..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
END

echo "Starting server..."
exec "$@"
