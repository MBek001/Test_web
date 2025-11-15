#!/bin/bash

echo "========================================="
echo "Quiz Platform Setup Script"
echo "========================================="

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Creating database..."
python manage.py makemigrations
python manage.py migrate

# Create media directories
echo "Creating media directories..."
mkdir -p media/test_files

# Create superuser
echo ""
echo "========================================="
echo "Creating admin user..."
echo "========================================="
python manage.py createsuperuser

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "To start the server, run:"
echo "python manage.py runserver"
echo ""
echo "Admin panel: http://127.0.0.1:8000/admin/"
echo "User login: http://127.0.0.1:8000/"
echo ""
