# Bot Hosting Platform

Plateforme complète d'hébergement de bots Discord (Python ou Node.js) basée sur FastAPI, SQLite et un frontend HTML/CSS/JS vanilla.

## Fonctionnalités
- Authentification JWT (inscription, connexion, /me)
- Gestion des bots : création, upload zip, stockage du token, start/stop/restart
- Suivi des processus et des logs en fichier
- Frontend dark responsive (login/register, dashboard, détail + logs temps réel)
- Déploiement Docker prêt à l'emploi

## Démarrage rapide avec Docker
```bash
cd bot-hosting-platform
docker compose up --build -d
```
Le service écoute sur le port `8000` (configurable dans docker-compose). Accédez à `http://localhost:8000/`.

### Volumes et données
- `./data` : base SQLite
- `./bots` : code des bots des utilisateurs
- `./logs` : logs des processus

## Exécution locale (sans Docker)
```bash
cd bot-hosting-platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```
Puis ouvrez `http://localhost:8000`.

## Déploiement sur VPS Ubuntu
```bash
sudo apt update && sudo apt install -y git python3 python3-venv unzip
git clone <ce-repo>
cd bot-hosting-platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```
Exposez le port 8000 (ou placez un reverse proxy Nginx vers `http://127.0.0.1:8000`).

## API (extrait)
- POST `/api/auth/register`
- POST `/api/auth/login`
- GET `/api/auth/me`
- GET `/api/bots`
- POST `/api/bots`
- GET `/api/bots/{id}`
- PUT `/api/bots/{id}`
- DELETE `/api/bots/{id}`
- POST `/api/bots/{id}/start`
- POST `/api/bots/{id}/stop`
- POST `/api/bots/{id}/restart`
- GET `/api/bots/{id}/status`
- GET `/api/bots/{id}/logs?lines=100`

## Sécurité
- Mots de passe hashés (bcrypt via passlib)
- JWT signé (HS256, clé configurable via `SECRET_KEY`)

## Structure
```
bot-hosting-platform/
├─ backend/
├─ frontend/
├─ bots/
├─ logs/
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ start.sh
├─ README.md
```
