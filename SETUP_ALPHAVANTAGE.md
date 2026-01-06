# Step-by-Step: Setting Up Alpha Vantage

## Step 1: Get Your Free API Key

1. **Open your web browser**
2. **Go to:** https://www.alphavantage.co/support/#api-key
3. **Fill out the form:**
   - First Name: (type your first name)
   - Last Name: (type your last name)  
   - Email: (type your email address)
   - Organization: (you can leave this blank or type "Personal")
4. **Click the big orange button** that says "GET FREE API KEY"
5. **Check your email** (might be in spam folder)
6. **Copy the API key** - it looks like: `ABC123XYZ789` (a long string of letters and numbers)

---

## Step 2: Add API Key to Your Project

**Option A: Using Terminal (Easier)**

1. **Open Terminal**
2. **Type this command:**
   ```bash
   cd /Users/jonahortega/risklattice
   ```
3. **Type this command (replace YOUR_KEY_HERE with your actual key):**
   ```bash
   echo "ALPHAVANTAGE_API_KEY=YOUR_KEY_HERE" >> .env
   ```
   
   For example, if your key is ABC123, you'd type:
   ```bash
   echo "ALPHAVANTAGE_API_KEY=ABC123" >> .env
   ```

**Option B: Using a Text Editor**

1. **Open Finder**
2. **Go to:** `/Users/jonahortega/risklattice/`
3. **Look for a file called `.env`** (it might be hidden - press Cmd+Shift+. to show hidden files)
4. **Open it in TextEdit** (double-click)
5. **Add this line at the bottom:**
   ```
   ALPHAVANTAGE_API_KEY=YOUR_KEY_HERE
   ```
   (Replace YOUR_KEY_HERE with your actual API key)
6. **Save the file**

---

## Step 3: Restart Docker

**In Terminal, press `Ctrl + C` to stop Docker, then type:**

```bash
cd /Users/jonahortega/risklattice && docker-compose up --build
```

**Wait 2-3 minutes for it to build.**

---

## Step 4: Test It!

1. **Open:** http://localhost:3000
2. **Click "Refresh All"**
3. **Wait 30 seconds**
4. **You should see real data!** 🎉

---

## Important Notes:

- **Free tier allows 5 API calls per minute** - so if you refresh too fast, wait 1 minute
- **The API key is free forever** - no credit card needed
- **Data is real and live!**

---

## If Something Goes Wrong:

**Check your Terminal logs** - if you see "ALPHAVANTAGE_API_KEY not set", it means the key wasn't added correctly. Try Step 2 again!

