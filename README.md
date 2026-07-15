# Videoflix

A Django-based video streaming platform with JWT authentication and HLS video streaming.

## Tech Stack

- **Django** + **Django REST Framework** — backend API
- **PostgreSQL** — database
- **Redis** + **django-rq** — background job queue for video transcoding
- **ffmpeg** — video transcoding to HLS format
- **Gunicorn** — production WSGI server
- **Whitenoise** — static file serving
- **Docker** + **Docker Compose** — containerized deployment

---

## Features

- User registration with email activation
- JWT authentication via httpOnly cookies
- Password reset via email
- Video streaming via HLS (HTTP Live Streaming)
- Admin panel for video uploads with automatic transcoding to 360p, 720p, and 1080p

---

## Project Structure

```
videoflix/
├── core/                   # project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── auth_app/               # authentication
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── authentication.py   # cookie-based JWT authentication
│   ├── models.py           # custom user model
│   └── tokens.py           # token generators for activation and password reset
├── video_app/              # video streaming
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── admin.py            # video upload via Django admin
│   ├── models.py           # Video and Category models
│   ├── signals.py          # triggers transcoding on video upload
│   ├── tasks.py            # RQ background transcoding task
│   └── transcoder.py       # ffmpeg transcoding logic
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## Getting Started

### Prerequisites

- Docker Desktop

### Setup

1. Clone the repository:
    ```bash
    git clone <repo-url>
    cd videoflix
    ```

2. Create a `.env` file based on `.env.example`:
    ```bash
    cp .env.example .env
    ```

3. Fill in the required values in `.env` (see Configuration section below).

4. Build and start the containers:
    ```bash
    docker-compose up --build
    ```

The app will be available at `http://127.0.0.1:8000`.

On first start the entrypoint script automatically:
- Waits for PostgreSQL to be ready
- Runs migrations
- Creates a superuser from the `.env` credentials
- Starts the RQ worker for background transcoding
- Starts Gunicorn

### Stopping

```bash
docker-compose down        # stop containers, keep data
docker-compose down -v     # stop containers and wipe all data (database + media files)
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the values:

```env
# Django
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your_password
DJANGO_SUPERUSER_EMAIL=admin@example.com
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Database
DB_NAME=videoflix_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=db               # use 'db' for Docker, 'localhost' for local dev
DB_PORT=5432

# Redis
REDIS_HOST=redis         # use 'redis' for Docker, 'localhost' for local dev
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=your@email.com
```

Generate a secure `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/api/auth/register/` | Register a new user | No |
| GET | `/api/auth/activate/<uid>/<token>/` | Activate account via email link | No |
| POST | `/api/auth/login/` | Login and receive JWT cookies | No |
| POST | `/api/auth/logout/` | Logout and blacklist refresh token | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| POST | `/api/auth/password-reset/` | Request password reset email | No |
| POST | `/api/auth/password-reset-confirm/<uid>/<token>/` | Confirm and set new password | No |

### Videos

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| GET | `/api/video/` | List all available videos | Yes |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | Get HLS playlist for a video | Yes |
| GET | `/api/video/<id>/<resolution>/<segment>/` | Get HLS video segment | Yes |

Available resolutions: `360p`, `720p`, `1080p`

---

## Authentication

The API uses JWT authentication via httpOnly cookies. After login, two cookies are set automatically:

- `access_token` — short-lived, used to authenticate requests
- `refresh_token` — longer-lived, used to obtain new access tokens

All video endpoints require a valid `access_token` cookie. If the access token expires, call `/api/auth/token/refresh/` to get a new one.

---

## Video Management

Videos are managed through the Django admin panel at `http://127.0.0.1:8000/admin/`.

When an admin uploads a video:
1. The raw file is saved to `/app/media/uploads/`
2. A background RQ job is queued via Redis
3. ffmpeg transcodes the video to HLS format at three resolutions
4. HLS segments are saved to `/app/media/hls/<video_id>/<resolution>/`
5. The video's `hls_ready` flag is set to `True`
6. The video becomes available via the streaming endpoints

---

## Running with Docker

### First time setup
```bash
docker-compose up --build
```

### Starting and stopping
```bash
docker-compose up          # start all containers
docker-compose down        # stop containers, keep data
docker-compose down -v     # stop containers and wipe all data
```

### Useful commands
```bash
docker-compose logs web              # view Django logs
docker-compose logs worker           # view RQ worker logs
docker-compose ps                    # list running containers
docker-compose exec web bash         # open a shell inside the Django container
docker-compose exec web python manage.py shell   # open Django shell
```

### Rebuilding
Only needed when you change `Dockerfile`, `requirements.txt`, or `backend.entrypoint.sh`:
```bash
docker-compose down
docker-compose up --build
```

For Python code changes (views, models, serializers) no rebuild is needed — the local folder is mounted directly into the container so changes reflect immediately.

---

## Local Development (without Docker)

If running without Docker, install the following system dependencies:

```bash
brew install postgresql@15 redis ffmpeg
brew services start postgresql@15
brew services start redis
```

Update `.env`:
```env
DB_HOST=localhost
REDIS_HOST=localhost
REDIS_LOCATION=redis://localhost:6379/1
```

Run the server:
```bash
# terminal 1
python manage.py runserver

# terminal 2
python manage.py rqworker default
```

---

## Email

In development, emails are printed to the console:
```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

For production, configure a real SMTP provider such as SendGrid, Mailgun, or Gmail in your `.env`.