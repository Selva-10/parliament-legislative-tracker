#!/usr/bin/env python3
import subprocess, sys, os
print("Setting up Parliament Tracker...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
subprocess.run([sys.executable, "manage.py", "migrate"])
subprocess.run([sys.executable, "manage.py", "createsuperuser"])
subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"])
subprocess.run([sys.executable, "manage.py", "scrape_data", "--source=prs"])
print("Done. Run: python manage.py runserver")