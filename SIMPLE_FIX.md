# Quick Fix - Data Not Loading

The issue is the database connection. You have 2 options:

## Option 1: Keep Database in Docker (Easiest)

Just run the database in Docker, backend/frontend locally:

1. **Start just the database:**
   ```bash
   cd /Users/jonahortega/risklattice
   docker-compose up postgres -d
   ```

2. **Then run backend locally:**
   ```bash
   cd /Users/jonahortega/risklattice/backend
   python3 -m uvicorn main:app --reload --port 8000
   ```

3. **Run frontend (new terminal):**
   ```bash
   cd /Users/jonahortega/risklattice/frontend
   npm run dev
   ```

The database URL is now fixed to use `localhost` instead of `postgres`.

---

## Option 2: Check Backend Terminal for Errors

Look at your backend terminal - do you see any error messages? Share what you see and I can help fix it!
