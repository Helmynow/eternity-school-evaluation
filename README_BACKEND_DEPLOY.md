# Backend deployment (recommended)

Vercel Serverless Functions have a **250MB unzipped** limit. This project’s FastAPI backend depends on scientific/data libraries (e.g. `numpy`, `pandas`) which typically exceed that limit once packaged.

The production-safe solution is:

1) Deploy the **frontend** on Vercel (static).
2) Deploy the **backend** as a separate service (Docker/container).
3) Point the frontend to the backend using `VITE_API_URL`.

## Deploy backend with Docker

Build:

```bash
docker build -f Dockerfile.backend -t ese-backend .
```

Run:

```bash
docker run --rm -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="postgresql://..." \
  -e REQUIRE_SUPABASE_AUTH=true \
  -e SUPABASE_URL="https://<project>.supabase.co" \
  -e SUPABASE_ANON_KEY="..." \
  -e SUPABASE_SERVICE_ROLE_KEY="..." \
  -e SUPABASE_JWT_SECRET="..." \
  ese-backend
```

## Configure Vercel frontend

Set these environment variables in the Vercel Project settings:

- `VITE_API_URL` = `https://<your-backend-host>` (example: `https://api.eternityschoolegypt.com`)

After setting env vars, redeploy the Vercel frontend.

## Notes

- The frontend calls endpoints like `/api/v2/...`; with `VITE_API_URL` set, requests become `https://<backend-host>/api/v2/...`.
- If you want, I can add a small `/health` check page in the frontend that validates connectivity to `VITE_API_URL` and shows a friendly error if it’s misconfigured.
