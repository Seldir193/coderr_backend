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

