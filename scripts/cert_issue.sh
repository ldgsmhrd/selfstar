#!/usr/bin/env sh
set -euo pipefail

# Issue initial certificate for selfstar.duckdns.org using webroot via docker compose certbot
EMAIL=${EMAIL:-"chani7873@daum.net"}
DOMAIN=${DOMAIN:-"selfstar.duckdns.org"}

echo "Issuing Let's Encrypt cert for $DOMAIN with email $EMAIL"
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --agree-tos --no-eff-email -m "$EMAIL"

echo "Reloading nginx to pick up new certs"
docker compose exec nginx nginx -s reload || true
