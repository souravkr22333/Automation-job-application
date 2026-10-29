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

## Railway deployment

Set the FastAPI service root directory to `Backend/fastapi_app` and select the **Dockerfile** builder. The included `Dockerfile` installs the matching Playwright Chromium binary and its Linux system dependencies into the image at build time. Redeploy after changing the builder/root directory.

For a manual deployment without Docker, install the browser after installing `requirements.txt`:

```powershell
python -m playwright install --with-deps chromium
```

The deployment must use the same Playwright package version as `requirements.txt` when installing the browser binary.

## Operational limitations

The submitter uses generic page selectors and cannot reliably complete every company's application form. It does not persist authenticated browser sessions; sites that require sign-in (including LinkedIn redirects) will fail rather than submit. Review queue results and verify uncertain submissions before retrying, especially those marked `pending_confirmation`, to avoid duplicate applications.
