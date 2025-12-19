# Deployment (Raspberry Pi 5) — Coderr
Dieses Dokument beschreibt, wie **Coderr** auf einem Raspberry Pi 5 (Debian / Raspberry Pi OS) produktionsnah deployed wird.
> Wichtig: **Frontend-Code wird nicht verändert.** Das Frontend nutzt die API fest über `https://api.selcuk-kocyigit.de/api/`.
---
## Ziel-Setup (Architektur)
- **Frontend (statisch):** `https://coderr.selcuk-kocyigit.de`
  - Nginx liefert HTML/CSS/JS aus: `/var/www/coderr_frontend`
- **Backend (Django/DRF):** `https://api.selcuk-kocyigit.de`
  - Nginx Reverse Proxy → Gunicorn auf `127.0.0.1:8000`
  - Admin: `https://api.selcuk-kocyigit.de/admin/`
  - API: `https://api.selcuk-kocyigit.de/api/...`
- **Static/Media (Backend):**
  - `/static/` → `/home/pi/coderr_backend/staticfiles/`
  - `/media/`  → `/home/pi/coderr_backend/media/`
- **SSL:** Let’s Encrypt (certbot) für beide Subdomains
- **Firewall:** UFW aktiv (nur 22/80/443)
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)
---
## Inhalt
- [Ziel-Setup (Architektur)](#ziel-setup-architektur)
- [Voraussetzungen](#voraussetzungen)
- [Server vorbereiten (Pi)](#server-vorbereiten-pi)
- [Backend deployen](#backend-deployen)
- [Systemd Service (Gunicorn)](#systemd-service-gunicorn)
- [Frontend deployen](#frontend-deployen)
- [Nginx Konfiguration](#nginx-konfiguration)
- [SSL mit Certbot](#ssl-mit-certbot)
- [Checks](#checks)

---
## Voraussetzungen
### DNS (All-Inkl)
A-Records auf die **öffentliche IP** des Heimanschlusses setzen:
- `coderr` → `<PUBLIC_IP>`
- `api` → `<PUBLIC_IP>`

### DNS-Propagation prüfen (gegen 8.8.8.8)
```bash
nslookup api.selcuk-kocyigit.de 8.8.8.8
nslookup coderr.selcuk-kocyigit.de 8.8.8.8
```
### Router / Portfreigabe
Weiterleitungen auf die lokale IP des Raspberry Pi:
- TCP 80  → `<PI_LAN_IP>`
- TCP 443 → `<PI_LAN_IP>`
> UDP bleibt frei.
---
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)

## Server vorbereiten (Pi)
### Pakete installieren (System, Nginx, Python, Certbot, Tools)
```bash
sudo apt update
sudo apt install -y nginx git python3-venv python3-pip python3-dev \
  certbot python3-certbot-nginx rsync ufw dnsutils

```
### Firewall konfigurieren (UFW)
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)




## Backend deployen
### Backend-Repository klonen
```bash
cd ~
git clone git@github.com:Seldir193/coderr_backend.git
cd coderr_backend
```
### Virtuelle Umgebung erstellen & aktivieren
```bash
python3 -m venv .venv
source .venv/bin/activate
```
### Dependencies installieren
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
### Datenbank migrieren
```bash
python manage.py migrate
```
### Static Files sammeln (collectstatic)
```bash
python manage.py collectstatic --noinput
deactivate
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)





## Systemd Service (Gunicorn)
### Systemd Service-Datei erstellen/öffnen
```bash
sudo nano /etc/systemd/system/coderr.service
```

### Systemd Service-Inhalt (Gunicorn)
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

### Systemd Service laden & starten (Coderr/Gunicorn)
```bash
sudo systemctl daemon-reload
sudo systemctl enable coderr
sudo systemctl start coderr
sudo systemctl status coderr --no-pager
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)

## Frontend deployen
### Frontend-Repository klonen
```bash
cd ~
git clone git@github.com:Seldir193/coderr_frontend.git
```
### Frontend Zielverzeichnis erstellen
```bash
sudo mkdir -p /var/www/coderr_frontend
```
### Frontend deployen: Dateien synchronisieren & Rechte setzen
```bash
sudo rsync -a --delete /home/pi/coderr_frontend/ /var/www/coderr_frontend/
sudo chown -R www-data:www-data /var/www/coderr_frontend
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)



## Nginx Konfiguration

### Nginx Site-Konfiguration öffnen
```bash
sudo nano /etc/nginx/sites-available/coderr
```
### Nginx Konfiguration (Frontend + API)
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

### Nginx Site aktivieren & Default entfernen
```bash
sudo ln -sf /etc/nginx/sites-available/coderr /etc/nginx/sites-enabled/coderr
sudo rm -f /etc/nginx/sites-enabled/default
```
### Nginx Konfiguration testen & neu laden
```bash
sudo nginx -t
sudo systemctl reload nginx
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)



## SSL mit Certbot

### SSL Zertifikate erstellen (Certbot)
```bash
sudo certbot --nginx -d coderr.selcuk-kocyigit.de
sudo certbot --nginx -d api.selcuk-kocyigit.de
```
### Certbot Auto-Renew testen
```bash
sudo certbot renew --dry-run
```
### Zertifikate anzeigen
```bash
sudo certbot certificates
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)


## Checks

### Backend/Gunicorn neu starten
```bash
sudo systemctl restart coderr
```
### Ports prüfen (80/443)
```bash
sudo ss -tulpn | grep -E ':80|:443'
```
### HTTP Checks (Frontend, API, Admin)
```bash
curl -I https://coderr.selcuk-kocyigit.de/
curl -I https://api.selcuk-kocyigit.de/api/login/   # 405 ist OK (GET)
curl -I https://api.selcuk-kocyigit.de/admin/
```
[↑ Zurück zum Inhaltsverzeichnis](#inhalt)





