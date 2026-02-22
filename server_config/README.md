# Docstore production server config (Debian)

Deze map bevat voorbeeld-configuraties voor productie deploy op Debian/Ubuntu met Docker Compose + Nginx reverse proxy.

## Bestanden

- `docstore.service`: systemd service om de compose stack automatisch te starten bij boot.
- `docstore.deknijf.eu.conf`: Nginx vhost (reverse proxy) voor `docstore.deknijf.eu`.

## Verwachte paden op server

- Project map: `/home/admin/docstore`
- Compose file: `/home/admin/docstore/docker-compose.yml`
- Env file: `/home/admin/docstore/.env`

Pas deze paden aan in `docstore.service` als jouw serverlayout anders is.

## Deploy stappen (systemd + docker compose)

1. Kopieer service file:

```bash
sudo cp /home/admin/docstore/server_config/docstore.service /etc/systemd/system/docstore.service
```

2. Herlaad systemd en activeer service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable docstore.service
sudo systemctl start docstore.service
```

3. Controleer status:

```bash
sudo systemctl status docstore.service
```

4. Volg logs:

```bash
journalctl -u docstore.service -f
```

## Nginx reverse proxy

1. Kopieer de vhost config:

```bash
sudo cp /home/admin/docstore/server_config/docstore.deknijf.eu.conf /etc/nginx/sites-available/docstore.deknijf.eu.conf
```

2. Activeer de site:

```bash
sudo ln -s /etc/nginx/sites-available/docstore.deknijf.eu.conf /etc/nginx/sites-enabled/docstore.deknijf.eu.conf
```

3. Test en herlaad Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## SSL via Let's Encrypt (Certbot)

1. Installeer Certbot + Nginx plugin:

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

2. Vraag certificaat aan en laat Certbot Nginx aanpassen:

```bash
sudo certbot --nginx -d docstore.deknijf.eu
```

3. Controleer auto-renew:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

## .env productie checklist

Aanbevolen in productie:

- `ENVIRONMENT=production`
- `PUBLIC_BASE_URL=https://docstore.deknijf.eu`
- `ALLOWED_HOSTS=docstore.deknijf.eu`
- `TRUST_PROXY_HEADERS=true`
- `INTEGRATION_MASTER_KEY` wijzigen (niet default laten)

Opmerking:
- Zorg dat DNS van `docstore.deknijf.eu` naar je server-IP wijst.
- Poorten `80` en `443` moeten open staan in firewall/security group.

