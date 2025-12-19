# Deployment (Raspberry Pi 5) — Coderr
This document describes how to deploy **Coderr** on a Raspberry Pi 5 (Debian / Raspberry Pi OS) in a production-like setup.
> Important: **The frontend code will not be modified.** The frontend expects the API at **[API Offers](https://api.selcuk-kocyigit.de/api/offers/)**.
---
## Target Setup (Architecture)
- **Frontend (static):** [coderr.selcuk-kocyigit.de](https://coderr.selcuk-kocyigit.de)
  - Nginx serves HTML/CSS/JS from: `/var/www/coderr_frontend`
- **Backend (Django/DRF):** [api.selcuk-kocyigit.de](https://api.selcuk-kocyigit.de)
  - Nginx reverse proxy → Gunicorn on `127.0.0.1:8000`
  - Admin: [Admin](https://api.selcuk-kocyigit.de/admin/)
  - API: [API Offers](https://api.selcuk-kocyigit.de/api/offers/)
- **Static/Media (backend):**
  - `/static/` → `/home/pi/coderr_backend/staticfiles/`
  - `/media/`  → `/home/pi/coderr_backend/media/`
- **SSL:** Let’s Encrypt (certbot) for both subdomains
- **Firewall:** UFW enabled (only 22/80/443)
[↑ Back to Table of Contents](#table-of-contents)
---
## Table of Contents
- [Target Setup (Architecture)](#target-setup-architecture)
- [Prerequisites](#prerequisites)
- [Prepare the Server (Pi)](#prepare-the-server-pi)
- [Deploy Backend](#deploy-backend)
- [Systemd Service (Gunicorn)](#systemd-service-gunicorn)
- [Deploy Frontend](#deploy-frontend)
- [Nginx Configuration](#nginx-configuration)
- [SSL with Certbot](#ssl-with-certbot)
- [Checks](#checks)
---


## Prerequisites
### DNS (All-Inkl)
Point A-records to the **public IP** of your home internet connection:
- `coderr` → `<PUBLIC_IP>`
- `api` → `<PUBLIC_IP>`

### Check DNS propagation (via 8.8.8.8)
```bash
nslookup api.selcuk-kocyigit.de 8.8.8.8
nslookup coderr.selcuk-kocyigit.de 8.8.8.8
```
### Router / Port forwarding
Forward ports to the Raspberry Pi local IP:
- TCP 80  → `<PI_LAN_IP>`
- TCP 443 → `<PI_LAN_IP>`
> Leave UDP unused.

[↑ Back to Table of Contents](#table-of-contents)





## Prepare the Server (Pi)
### Install packages (system, Nginx, Python, Certbot, tools)
```bash
sudo apt update
sudo apt install -y nginx git python3-venv python3-pip python3-dev \
  certbot python3-certbot-nginx rsync ufw dnsutils
```
### Configure firewall (UFW)
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```
[↑ Back to Table of Contents](#table-of-contents)




## Deploy Backend
### Clone the backend repository
```bash
cd ~
git clone git@github.com:Seldir193/coderr_backend.git
cd coderr_backend
```
### Create & activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```
### Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
### Run database migrations
```bash
python manage.py migrate
```
### Collect static files (collectstatic)
```bash
python manage.py collectstatic --noinput
deactivate
```
[↑ Back to Table of Contents](#table-of-contents) 




## Systemd Service (Gunicorn)
### Create/open the systemd service file
```bash
sudo nano /etc/systemd/system/coderr.service
```
### Systemd service content (Gunicorn)
```ini
[Unit]
Description=Coderr Django App (Gunicorn)
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/coderr_backend
Environment="PATH=/home/pi/coderr_backend/.venv/bin"
ExecStart=/home/pi/coderr_backend/.venv/bin/gunicorn Coder.wsgi:application --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```
### Reload, enable & start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable coderr
sudo systemctl start coderr
sudo systemctl status coderr --no-pager
```
[↑ Back to Table of Contents](#table-of-contents) 





## Deploy Frontend
### Clone the frontend repository
```bash
cd ~
git clone git@github.com:Seldir193/coderr_frontend.git
```
### Create the frontend target directory
```bash
sudo mkdir -p /var/www/coderr_frontend
```
### Sync files & set permissions
```bash
sudo rsync -a --delete /home/pi/coderr_frontend/ /var/www/coderr_frontend/
sudo chown -R www-data:www-data /var/www/coderr_frontend
```
[↑ Back to Table of Contents](#table-of-contents) 




## Nginx Configuration 
### Open Nginx site config
```bash
sudo nano /etc/nginx/sites-available/coderr
```
### Nginx config (Frontend + API)
```nginx
server {
    listen 80;
    server_name coderr.selcuk-kocyigit.de;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name coderr.selcuk-kocyigit.de;

    root /var/www/coderr_frontend;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    ssl_certificate /etc/letsencrypt/live/coderr.selcuk-kocyigit.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/coderr.selcuk-kocyigit.de/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

# ----------------------------
# API: api subdomain
# ----------------------------
server {
    listen 80;
    server_name api.selcuk-kocyigit.de;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.selcuk-kocyigit.de;

    location /static/ {
        alias /home/pi/coderr_backend/staticfiles/;
    }

    location /media/ {
        alias /home/pi/coderr_backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    ssl_certificate /etc/letsencrypt/live/api.selcuk-kocyigit.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.selcuk-kocyigit.de/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
```
### Enable site & remove default
```bash
sudo ln -sf /etc/nginx/sites-available/coderr /etc/nginx/sites-enabled/coderr
sudo rm -f /etc/nginx/sites-enabled/default
```
### Test config & reload Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```
[↑ Back to Table of Contents](#table-of-contents) 




## SSL with Certbot
### Create SSL certificates (Certbot)
```bash
sudo certbot --nginx -d coderr.selcuk-kocyigit.de
sudo certbot --nginx -d api.selcuk-kocyigit.de
```
### Test cert renewal (dry run)
```bash
sudo certbot renew --dry-run
```
### Show installed certificates
```bash
sudo certbot certificates
```
[↑ Back to Table of Contents](#table-of-contents)  






## Checks
### Restart backend (Gunicorn) 
```bash
sudo systemctl restart coderr
```
### Check open ports (80/443)
```bash
sudo ss -tulpn | grep -E ':80|:443'
```
### HTTP checks (Frontend, API, Admin)
```bash
curl -I https://coderr.selcuk-kocyigit.de/
curl -I https://api.selcuk-kocyigit.de/api/login/   # 405 is OK (GET)
curl -I https://api.selcuk-kocyigit.de/admin/
```
[↑ Back to Table of Contents](#table-of-contents) 
