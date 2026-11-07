"""Vercel WSGI entry point. Credentials come from server environment variables."""
from footfall.app import create_app

app = create_app()
