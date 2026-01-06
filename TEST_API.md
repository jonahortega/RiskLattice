# Quick Test - Check If API Key Works

## Test if API is Working:

**Open your browser and go to:**
```
http://localhost:8000/api/test/AAPL
```

**You should see one of these:**

✅ **If it works:** You'll see JSON with `"test": "success"` and a `current_price`

❌ **If API key not set:** You'll see `"api_key_configured": false`

❌ **If rate limited:** You'll see an error about rate limits

❌ **If other error:** You'll see the error message

**Please tell me what you see when you open that URL!**

