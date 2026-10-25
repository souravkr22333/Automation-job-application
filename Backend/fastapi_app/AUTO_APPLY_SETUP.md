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

## Install the browser

Install the Chromium browser binary in the FastAPI deployment environment after installing `requirements.txt`:

```powershell
python -m playwright install chromium
```

The runtime environment must include the system libraries required by Playwright Chromium. Use the Playwright browser installation instructions for the host OS/container when deploying to Linux.

## Operational limitations

The submitter uses generic page selectors and cannot reliably complete every company's application form. It does not persist authenticated browser sessions; sites that require sign-in (including LinkedIn redirects) will fail rather than submit. Review queue results and verify uncertain submissions before retrying, especially those marked `pending_confirmation`, to avoid duplicate applications.
