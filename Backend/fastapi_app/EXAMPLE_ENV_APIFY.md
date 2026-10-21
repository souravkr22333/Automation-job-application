# Apify env setup (FastAPI)

Your FastAPI app reads Apify settings from `Backend/fastapi_app/app/config.py`.

## 1) Required: API token
Create/edit: `Backend/fastapi_app/.env`

```env
APIFY_API_TOKEN=YOUR_APIFY_API_TOKEN_HERE
```

## 2) Optional: default actor
If you want to force which Apify Actor is used by default, add:

```env
APIFY_DEFAULT_ACTOR=jungle_thunder~linkedin-jobs-scraper-free-trial
```

If you do not set `APIFY_DEFAULT_ACTOR`, your code falls back to the actor hardcoded in
`Backend/fastapi_app/app/scrapers/apify_service.py`.

## 3) After updating .env
Restart FastAPI and run:

```bat
python Backend\fastapi_app\test_scraper.py
```

## Notes
- Your adapter expects dataset items formatted with at least:
  - `title`
  - `company`
  - `url` (job link)
- If you get HTTP 500 or `jobs_found: 0`, the issue is either:
  - the actor run failed (auth/input/actor permissions)
  - or the actor succeeded but returned empty dataset items.

