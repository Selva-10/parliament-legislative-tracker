@echo off
cd "C:\Users\acer\OneDrive\Desktop\My Project 2\Parliament-Tracker"
call venv\Scripts\activate
python manage.py auto_scrape --daemon
pause