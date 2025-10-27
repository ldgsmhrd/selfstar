#!/usr/bin/env sh
set -euo pipefail

echo "Renewing Let's Encrypt certs (if due)"
docker compose run --rm certbot renew --webroot -w /var/www/certbot
echo "Reloading nginx to pick up renewed certs"
docker compose exec nginx nginx -s reload || true
