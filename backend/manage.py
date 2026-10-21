#!/usr/bin/env python3
"""Django management entry point; caller must select settings explicitly."""
import os
import sys
from django.core.management import execute_from_command_line
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    raise SystemExit("DJANGO_SETTINGS_MODULE is required")
if __name__ == "__main__":
    execute_from_command_line(sys.argv)
