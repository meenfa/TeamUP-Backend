# TeamUp Backend MVP

Backend MVP for TeamUp, a futsal game coordination and player matching platform built with Django, Django REST Framework, PostgreSQL, Redis, Celery, and Google sign-in.

## What this backend supports

- Google authentication with backend ID token verification
- JWT authentication stored in HTTP-only cookies
- profile management
- public profile lookup by username
- game creation, update, discovery, filtering, search, and pagination
- join and leave game flows
- attendance confirmation
- host-side participant approval, rejection, and status marking
- no-show penalties and reliability scoring
- temporary restriction after repeated no-shows
- post-game ratings
- in-app notifications
- Celery-backed background tasks

## Tech stack

- Python 3.11+
- Django 5
- Django REST Framework
- SimpleJWT
- PostgreSQL
- Redis
- Celery
- Google Auth
- Gunicorn
- Nginx
- python-dotenv

## Project structure

```text
teamup_backend_mvp/
|-- accounts/
|   |-- auth/
|   |-- auth_urls.py
|   |-- authentication.py
|   |-- managers.py
|   |-- models.py
|   |-- profile_urls.py
|   |-- serializers.py
|   |-- services.py
|   |-- signals.py
|   |-- tasks.py
|   `-- views.py
|-- common/
|   |-- constants.py
|   |-- exceptions.py
|   |-- mixins.py
|   `-- pagination.py
|-- config/
|   |-- asgi.py
|   |-- celery.py
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|-- deploy/
|   |-- celery.service.example
|   |-- celerybeat.service.example
|   |-- gunicorn.service.example
|   `-- nginx.teamup.conf.example
|-- games/
|-- notifications/
|-- ratings/
|-- .env.example
|-- manage.py
|-- requirements.txt
`-- README.md
```

## Architecture notes

- `accounts`: custom user model, Google auth, cookie JWT auth, profile data, restriction logic
- `games`: game lifecycle, participation, attendance, host actions, personal game lists
- `ratings`: post-game trust and honesty ratings
- `notifications`: in-app notification records and background reminder tasks
- `common`: shared constants, pagination, exception formatting, and response helpers

Business logic lives mainly in service modules so the views stay thin.

## Authentication model

This backend does not use Resend-based auth flows or email/password login endpoints.

Authentication works like this:

1. The frontend obtains a Google ID token.
2. The frontend sends that token to `POST /api/auth/google/`.
3. The backend verifies the token with Google.
4. The backend creates or updates the user.
5. The backend issues SimpleJWT access and refresh tokens as HTTP-only cookies.
6. Protected API endpoints read the access token from the `access` cookie through `accounts.authentication.CookieJWTAuthentication`.

Cookie names:

- `access`
- `refresh`

Current auth endpoints:

- `POST /api/auth/google/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`

Current limitation:

- protected requests use the `access` cookie automatically
- refresh and logout are not fully cookie-native yet and still depend on the refresh token value being submitted to the backend flow

## Important MVP design choices

### Reliability score

The reliability score starts at `100.00`.

- attended game: `+1.50`
- no-show: `-12.50`
- minimum: `0.00`
- maximum: `100.00`

### Temporary restriction(Optional)

When a user reaches `3` no-shows, the system applies a `14` day restriction and blocks that user from joining new games until it expires.

Celery Beat runs an hourly task to clear expired restrictions.

### Reminders

When a user joins a game, a reminder task is scheduled for `GAME_REMINDER_LEAD_MINUTES` before the match. If that time has already passed, the reminder is created immediately.

## Environment variables

Copy `.env.example` to `.env` and adjust the values.

Important variables:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
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
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GAME_REMINDER_LEAD_MINUTES`
- `DEFAULT_FROM_EMAIL`

`DB_ENGINE=sqlite` is supported only as a lightweight local fallback. Main intended runtime is PostgreSQL.

## Local setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS or Linux:

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

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

Then update `.env` with your values.

### 4. PostgreSQL setup

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

### 7. Create an admin user

```bash
python manage.py createsuperuser
```

### 8. Run the Django server

```bash
python manage.py runserver
```

### 9. Run Celery worker

```bash
celery -A config worker -l info
```

### 10. Run Celery Beat

```bash
celery -A config beat -l info
```

## API overview

Base path: `/api/`

### Auth

- `POST /api/auth/google/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`

### Profile

- `GET /api/profile/`
- `PATCH /api/profile/`
- `GET /api/profile/{username}/`

### Games

- `GET /api/games/`
- `POST /api/games/`
- `GET /api/games/{id}/`
- `PATCH /api/games/{id}/`
- `POST /api/games/{id}/join/`
- `POST /api/games/{id}/leave/`
- `POST /api/games/{id}/confirm-attendance/`
- `POST /api/games/{id}/approve-participant/`
- `POST /api/games/{id}/reject-participant/`
- `POST /api/games/{id}/mark-participant-status/`
- `GET /api/my-games/`

### Ratings

- `POST /api/ratings/`
- `GET /api/ratings/me/`

### Notifications

- `GET /api/notifications/`

## Sample request flows

### Google auth

```json
POST /api/auth/google/
{
  "credential": "<google-id-token>"
}
```

Successful response:

```json
{
  "success": true,
  "message": "Google login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "alice@example.com",
      "full_name": "Alice Sharma",
      "username": "alice-sharma-ab12cd"
    }
  }
}
```

Auth tokens are set in HTTP-only cookies by the backend.

### Refresh token

```json
POST /api/auth/token/refresh/
{
  "refresh": "<refresh-token>"
}
```

This endpoint is currently the default SimpleJWT refresh view.

### Logout

```json
POST /api/auth/logout/
{
  "refresh": "<refresh-token>"
}
```

The backend blacklists the refresh token and clears the auth cookies.

### Update profile

```json
PATCH /api/profile/
{
  "full_name": "Alice Sharma",
  "city": "Kathmandu",
  "preferred_area": "Baneshwor",
  "skill_level": "mixed",
  "bio": "Weekend futsal player"
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

### Mark participant status

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
- backend Google token verification
- JWT access token read from HTTP-only cookies
- refresh token blacklist on logout
- database-backed duplicate join protection
- host-only participant management actions
- atomic transactions on concurrency-sensitive flows
- environment-based secret management
- CORS credentials enabled for cookie auth
- permission checks on writable game actions

## Production deployment on a VPS

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

Use production values for:

- `DEBUG=False`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- PostgreSQL settings
- Redis settings
- `GOOGLE_OAUTH_CLIENT_ID`

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

Copy them into `/etc/systemd/system/`, adjust paths, then run:

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

Then run:

```bash
sudo ln -s /etc/nginx/sites-available/teamup /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Add TLS

Use Certbot for HTTPS:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

For production cookie auth, review your cookie `Secure`, `SameSite`, CORS, CSRF, and proxy settings carefully.

## Notes for future improvement

- make refresh flow fully cookie-native end to end
- remove stale auth-related env variables if they are no longer needed
- add automated tests for cookie refresh and logout flows
- add WebSocket or push notifications
- add richer analytics and admin dashboards
- add CI for tests and deploy checks
