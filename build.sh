#!/bin/bash
set -e

echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Running database migrations..."
python manage.py migrate

echo "Setting up Google OAuth provider..."
python manage.py setup_google_oauth || echo "⚠ Warning: Google OAuth setup encountered an issue (continuing...)"

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "✅ Build completed successfully!"
