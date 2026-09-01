#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.core.management import call_command

try:
    print("Running migrations...")
    call_command('migrate', verbosity=2)
    print("✅ Migrations completed successfully!")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
