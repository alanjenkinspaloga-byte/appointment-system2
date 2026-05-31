#!/usr/bin/env bash
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Optional: Run setup command for Google OAuth (if not already configured)
# python manage.py setup_google_oauth

echo "✓ Build script completed successfully"
