# Quickest Way to See Changes

## Option 1: Just Refresh Browser (if using Docker)
If you're running Docker, the changes are already loaded! Just:
1. **Refresh your browser** (hard refresh: Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

## Option 2: Run Backend Locally (Simpler - No Docker)

### Step 1: Stop Docker (if running)
Just close the terminal where Docker is running, or press `Ctrl+C`

### Step 2: Run Backend Locally
Open a terminal and run:

```bash
cd /Users/jonahortega/risklattice/backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Run Frontend (in another terminal)
Open a NEW terminal and run:

```bash
cd /Users/jonahortega/risklattice/frontend
npm run dev
```

### Step 4: Open Browser
Go to: http://localhost:3000

**That's it!** The backend will auto-reload when you make code changes (because of `--reload` flag).

