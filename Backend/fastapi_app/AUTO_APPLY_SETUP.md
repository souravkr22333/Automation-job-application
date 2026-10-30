# Auto-apply service setup

Auto-apply is a two-service flow: Django tails and stores a resume, then calls the FastAPI service to download that tailored PDF and attempt the application through Playwright.

## Required environment

Set these variables on both the Django and FastAPI services:

```text
AUTO_APPLY_INTERNAL_TOKEN=<same-long-random-secret-on-both-services>
```

Set these variables on Django:

```text
FASTAPI_BASE_URL=http://localhost:8001
```

For deployment, set `FASTAPI_BASE_URL` to the private/reachable base URL of the FastAPI service. The FastAPI service must also have the required existing AI and Supabase credentials configured for resume tailoring and PDF storage.

Generate a token locally with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Do not commit the token to the repository or expose it to the frontend.

## Railway deployment without Docker

Set the FastAPI service root directory to `Backend/fastapi_app` and use the Nixpacks builder. The `nixpacks.toml` file installs Chromium's Linux shared-library dependencies into the runtime image. Set the build command to:

```sh
python -m pip install -r requirements.txt && PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright python -m playwright install chromium
```

Set `PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright` in the FastAPI service variables as well, so Playwright uses the same browser directory at runtime. Use the Procfile start command and clear the build cache before redeploying. Confirm the build logs show the Chromium install finishing successfully.

## Operational limitations

The submitter uses generic page selectors and cannot reliably complete every company's application form. It does not persist authenticated browser sessions; sites that require sign-in (including LinkedIn redirects) will fail rather than submit. Review queue results and verify uncertain submissions before retrying, especially those marked `pending_confirmation`, to avoid duplicate applications.
