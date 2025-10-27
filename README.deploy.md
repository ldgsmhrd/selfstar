# selfstar-deploy

Infrastructure-lite deployment stack for https://selfstar.duckdns.org using:
- Nginx (reverse proxy, TLS termination)
- FastAPI backend (uvicorn) from `../selfstar-app/backend`
- Frontend (Vite dev/preview server) from `../selfstar-app/frontend`
- Let's Encrypt (certbot) with HTTP-01 challenge

This gets you live quickly. For production hardening, see the notes at the end to serve a static frontend build directly from Nginx.

## Prerequisites

- A Linux host with Docker and Docker Compose plugin installed
- DNS A record: `selfstar.duckdns.org` -> your server public IP
- Open ports: 80/tcp and 443/tcp from the internet

## Files

- `docker-compose.yml`: Defines services: `nginx`, `backend`, `frontend`, and `certbot`
- `nginx/conf.d/selfstar.conf`: Nginx vhost with HTTP->HTTPS redirect, ACME challenge, reverse proxy rules
- `prod.env`: Environment for backend (you create from template)

## 1) Prepare environment

Copy the template and fill in values:

```
cp prod.env.example prod.env
# Edit prod.env to set DB credentials, SESSION_SECRET, OAuth keys, etc.
```

Minimum required values:
- `SESSION_SECRET`: long random string
- `FRONTEND_URL=https://selfstar.duckdns.org`
- `BACKEND_URL=https://selfstar.duckdns.org`
- Any DB connection variables your backend expects

## 2) Choose environment: dev vs prod

Dev (local, no TLS, ports on localhost):

```
# Windows PowerShell (from selfstar-deploy)
# Prepare env files (copy examples)
New-Item -ItemType Directory -Force -Path .\env | Out-Null
Copy-Item .\env\backend.env.example .\env\backend.env
Copy-Item .\env\frontend.env.example .\env\frontend.env
Copy-Item .\env\ai.env.example .\env\ai.env

# Edit .\env\backend.env to use localhost URLs for dev:
# FRONTEND_URL=http://localhost:5174
# BACKEND_URL=http://localhost:8000
# AI_BASE_URL=http://localhost:8600

docker compose -f docker-compose.dev.yml up -d --build
```

Prod (server, with Nginx and TLS):

```
# Prepare env files
mkdir -p env
cp env/backend.env.example env/backend.env
cp env/frontend.env.example env/frontend.env
cp env/ai.env.example env/ai.env

# Edit env/backend.env with production URLs:
# FRONTEND_URL=https://selfstar.duckdns.org
# BACKEND_URL=https://selfstar.duckdns.org
# AI_BASE_URL=http://selfstar-ai:8600
# First bring up Nginx/backend/frontend (HTTP only for ACME challenge)
docker compose up -d nginx backend frontend
```

This allows the ACME HTTP-01 challenge to be served. Existing certificates on the host are reused because `/etc/letsencrypt` is bind-mounted into the containers.

```
docker compose up -d nginx backend frontend
```

Verify `http://selfstar.duckdns.org` loads (it will be HTTP and show the app via Nginx). If DNS just changed, wait for propagation.

## 3) Obtain/renew TLS certificates (Let's Encrypt)

Run certbot one-off with webroot challenge (email preset to chani7873@daum.net in helper script). If certificates already exist under `/etc/letsencrypt/live/selfstar.duckdns.org`, this step can be skipped.

```
./scripts/cert_issue.sh
```

After success, reload Nginx to pick up the certs:

```
docker compose exec nginx nginx -s reload
```

Renewal (cron/monthly):

```
./scripts/cert_renew.sh
```

## 4) Full up

```
docker compose up -d
```

## CORS and cookies

Backend reads `FRONTEND_URL` and `BACKEND_URL` from env. They are pre-set for this domain in compose. Ensure `SESSION_SECRET` is set and keep it secret.

## Health check

- Backend: `https://selfstar.duckdns.org/health`
- Routes debug: `https://selfstar.duckdns.org/__routes`

## Logs

```
docker compose logs -f nginx
docker compose logs -f backend
docker compose logs -f frontend
```

## Hardening and improvements

- Serve a static frontend build from Nginx for better performance/security:
  - Build the frontend: `docker build -f Dockerfile -t selfstar-frontend:build ../selfstar-app/frontend` and copy `dist/` into an Nginx image; or use a multi-stage Dockerfile that outputs `/usr/share/nginx/html`.
  - Update `nginx/conf.d/selfstar.conf` to serve `root /usr/share/nginx/html;` for `/`, and keep API locations proxied to backend.
- Restrict `client_max_body_size` as needed, add caching headers for static assets.
- Add automatic cert renew (cron/systemd timer) to run `certbot renew` monthly. Because `/etc/letsencrypt` is bind-mounted, certs persist on the host and are shared with Nginx.

## Autostart on reboot (systemd)

Files under `systemd/` are provided to auto-start the stack and renew certificates.

1) Edit the WorkingDirectory paths in the unit files to the actual path on your server (e.g., `/opt/selfstar/selfstar-deploy`).

2) Install and enable the main service:

```
sudo cp systemd/selfstar.service /etc/systemd/system/selfstar.service
sudo systemctl daemon-reload
sudo systemctl enable --now selfstar.service
# Verify
systemctl status selfstar.service
docker compose ps
```

3) Optional: enable monthly cert renew via systemd timer:

```
sudo cp systemd/selfstar-cert-renew.service /etc/systemd/system/
sudo cp systemd/selfstar-cert-renew.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now selfstar-cert-renew.timer
# Verify next run
systemctl list-timers | grep selfstar-cert-renew
```

Note: Containers use `restart: unless-stopped` so they restart after Docker daemon restarts. The systemd unit ensures the compose project is brought up after a full host reboot.
- If you also deploy the AI service, add a service (port 8600) and map a path (e.g., `/ai/`) to it in Nginx.

## Troubleshooting

- 404 on ACME challenge: ensure `/.well-known/acme-challenge/` is served by Nginx from `/var/www/certbot` and port 80 is open.
- Mixed content or CORS: confirm envs `FRONTEND_URL` and `BACKEND_URL` are https and match the domain.
- 502/504 from Nginx: check `backend`/`frontend` container health and logs; adjust `proxy_read_timeout` if long-running requests are expected.