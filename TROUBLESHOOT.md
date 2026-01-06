# Quick Fix for "Not Found" Error

The frontend needs to reconnect to the backend. Here's what to do:

## Step 1: Stop Docker
In your Terminal, press `Ctrl + C` to stop everything

## Step 2: Restart Docker
Run this command:
```bash
cd /Users/jonahortega/risklattice && docker-compose up --build
```

Wait for it to fully start (you'll see "Application started")

## Step 3: Check Backend
In a new browser tab, open:
http://localhost:8000/api/health

You should see: `{"status":"healthy","service":"risklattice"}`

If that works, the backend is fine!

## Step 4: Check Frontend API Connection
Open your browser's Developer Tools (F12 or right-click → Inspect)
Go to the "Console" tab
Try adding a ticker again
Look for any error messages in red

The error will tell us exactly what's wrong!

