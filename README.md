# TeamUp Backend MVP

Production-minded backend MVP for **TeamUp**, a futsal game coordination and player matching platform built with Django, Django REST Framework, PostgreSQL, Redis, Celery, and JWT.

## What this backend supports

- user registration
- email verification links sent through Resend
- JWT authentication with refresh + blacklist logout
- profile management
- game creation, update, discovery, search, filtering, and pagination
- join and leave game flows
- attendance confirmation
- host-side participant status marking
- no-show penalties and reliability scoring
- temporary restriction after repeated no-shows
- post-game rating system
- in-app notifications
- Celery-backed async verification-email and reminder jobs

## Tech stack

- Python 3.11+
- Django 5
- Django REST Framework
- SimpleJWT
- PostgreSQL
- Redis
- Celery
- Gunicorn
- Nginx
- python-dotenv

## Project structure

```text
teamup_backend/
├── accounts/
│   ├── auth_urls.py
│   ├── profile_urls.py
│   ├── managers.py
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── signals.py
│   ├── tasks.py
│   └── views.py
├── common/
│   ├── constants.py
│   ├── exceptions.py
│   ├── mixins.py
│   └── pagination.py
├── config/
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── games/
│   ├── filters.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── services.py
│   └── views.py
├── notifications/
│   ├── models.py
│   ├── tasks.py
│   ├── utils.py
│   └── views.py
├── ratings/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   └── views.py
├── deploy/
│   ├── gunicorn.service.example
│   ├── celery.service.example
│   ├── celerybeat.service.example
│   └── nginx.teamup.conf.example
├── .env.example
├── manage.py
├── requirements.txt
└── README.md
```

## Architecture notes

The project uses modular Django apps so core business areas stay isolated:

- **accounts**: custom user model, profile, email verification, restriction logic, auth endpoints
- **games**: game lifecycle, participation, attendance, my games, filters
- **ratings**: trust and honesty ratings after games
- **notifications**: verification email delivery, join confirmations, reminders
- **common**: shared constants, pagination, exception format, response helpers

Business logic lives mainly in **services** instead of views. Views stay thin and focus on request/response behavior.

## Important MVP design choices

### 1. Reliability score

The reliability score starts at `100.00`.

- attended game: `+1.50`
- no-show: `-12.50`
- minimum: `0.00`
- maximum: `100.00`

This is intentionally simple and explainable for MVP use. The logic lives in `accounts/services.py`.

### 2. Temporary restriction

When a user reaches **3 no-shows**, the system creates a **14-day restriction** and prevents joining new games until it expires.

A Celery beat task clears expired restrictions hourly.

### 3. Email verification delivery

Verification emails are queued through Celery and delivered through the Resend Email API. If `RESEND_API_KEY` is not configured, the app logs the verification link and stores a fallback notification so local development can continue without a live sender.

### 4. Reminders

When a user joins a game, a reminder task is scheduled for `GAME_REMINDER_LEAD_MINUTES` before the match. If the reminder time is already in the past, the reminder is created immediately.

## Environment variables

Copy `.env.example` to `.env` and adjust the values.

Key variables:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `ACCESS_TOKEN_MINUTES`
- `REFRESH_TOKEN_DAYS`
- `RESEND_API_KEY`
- `EMAIL_VERIFICATION_URL`
- `EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS`
- `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS`
- `GAME_REMINDER_LEAD_MINUTES`
- `DEFAULT_FROM_EMAIL`

`DB_ENGINE=sqlite` is supported only as a lightweight local smoke-test fallback. For real usage and deployment use PostgreSQL.

## Local setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your own values.

### 4. PostgreSQL setup

Create database and user:

```sql
CREATE DATABASE teamup_db;
CREATE USER teamup_user WITH PASSWORD 'strong_password_here';
ALTER ROLE teamup_user SET client_encoding TO 'utf8';
ALTER ROLE teamup_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE teamup_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE teamup_db TO teamup_user;
```

Then set:

```env
DB_ENGINE=postgresql
DB_NAME=teamup_db
DB_USER=teamup_user
DB_PASSWORD=strong_password_here
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 5. Redis setup

Ubuntu example:

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping
```

Expected output:

```text
PONG
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create admin user

```bash
python manage.py createsuperuser
```

### 8. Run Django server

```bash
python manage.py runserver
```

### 9. Run Celery worker

```bash
celery -A config worker -l info
```

### 10. Run Celery beat

```bash
celery -A config beat -l info
```

## API overview

Base path: `/api/`

### Auth

- `POST /api/auth/register/`
- `GET /api/auth/verify-email/?token=...`
- `POST /api/auth/verify-email/`
- `POST /api/auth/resend-verification/`
- `POST /api/auth/login/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`

### Profile

- `GET /api/profile/`
- `PATCH /api/profile/`

### Games

- `GET /api/games/`
- `POST /api/games/`
- `GET /api/games/{id}/`
- `PATCH /api/games/{id}/`
- `POST /api/games/{id}/join/`
- `POST /api/games/{id}/leave/`
- `POST /api/games/{id}/approve-participant/`
- `POST /api/games/{id}/reject-participant/`
- `POST /api/games/{id}/confirm-attendance/`
- `POST /api/games/{id}/mark-participant-status/`
- `GET /api/my-games/`

### Ratings

- `POST /api/ratings/`
- `GET /api/ratings/me/`

### Notifications

- `GET /api/notifications/`

## Sample request flows

### Register

```json
POST /api/auth/register/
{
  "email": "alice@example.com",
  "phone_number": "+9779800000000",
  "full_name": "Alice Sharma",
  "password": "SecurePass123!"
}
```

### Verify email

```json
GET /api/auth/verify-email/?token=<signed-token>
```

### Resend verification email

```json
POST /api/auth/resend-verification/
{
  "email": "alice@example.com"
}
```

### Login

```json
POST /api/auth/login/
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}
```

### Create game

```json
POST /api/games/
{
  "location_name": "Baneshwor Futsal Arena",
  "area_city": "Kathmandu",
  "game_date": "2026-04-25",
  "start_time": "18:00:00",
  "end_time": "19:30:00",
  "total_players": 10,
  "skill_level": "mixed",
  "entry_fee": "500.00",
  "payment_note": "eSewa or cash",
  "description": "Friendly evening futsal game"
}
```

### Mark attendance result

```json
POST /api/games/{id}/mark-participant-status/
{
  "participant_user_id": 12,
  "status": "no_show"
}
```

## Filtering and search

`GET /api/games/` supports:

- `?area_city=Kathmandu`
- `?skill_level=beginner`
- `?status=open`
- `?game_date=2026-04-25`
- `?game_date_after=2026-04-20&game_date_before=2026-04-30`
- `?search=arena`
- `?ordering=game_date`

## Error format

Errors are normalized like this:

```json
{
  "success": false,
  "errors": {
    "detail": "Authentication credentials were not provided."
  }
}
```

## Security and validation highlights

- custom user model
- JWT access and refresh tokens
- refresh token blacklist logout
- signed email verification links with expiry
- resend cooldown protection
- duplicate join prevention with database constraint + service checks
- host-only participant management
- atomic transactions on concurrency-sensitive flows
- env-based secret management
- secure cookie flags outside debug mode
- permission checks on writable game actions

## Production deployment on a VPS (no Docker)

### 1. Install system packages

Ubuntu example:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip postgresql postgresql-contrib redis-server nginx
```

### 2. Upload project

Example target path:

```text
/srv/teamup_backend
```

### 3. Create venv and install requirements

```bash
cd /srv/teamup_backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure `.env`

Use production values:

- `DEBUG=False`
- strong `SECRET_KEY`
- real PostgreSQL credentials
- real `ALLOWED_HOSTS`
- real `CSRF_TRUSTED_ORIGINS`
- real Redis URLs

### 5. Run migrations and collect static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6. Test Gunicorn manually

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
```

### 7. Create systemd services

Use the examples in `deploy/`:

- `deploy/gunicorn.service.example`
- `deploy/celery.service.example`
- `deploy/celerybeat.service.example`

Copy them into `/etc/systemd/system/`, adjust paths, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl enable celery
sudo systemctl enable celerybeat
sudo systemctl start gunicorn
sudo systemctl start celery
sudo systemctl start celerybeat
```

### 8. Configure Nginx reverse proxy

Use `deploy/nginx.teamup.conf.example` as a base.

Then:

```bash
sudo ln -s /etc/nginx/sites-available/teamup /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Optional TLS

Use Certbot for HTTPS:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Notes for future improvement

- connect a real frontend verification success/failure page
- add payment gateway integration later
- add WebSocket or push notifications
- add game cancellation refund rules if payments become real
- add abuse moderation and fraud checks
- add richer analytics and admin dashboards
- add automated test suite and CI pipeline

## Smoke-tested status

The project was smoke-tested locally with Django migrations and a basic API flow using a temporary SQLite fallback. Main intended runtime remains PostgreSQL + Redis + Celery.
