# La Porrita - World Cup 2026

Web application for managing a World Cup 2026 betting pool. Import predictions from Excel, sync results with football-data.org, and display rankings/statistics.

## Features

- Excel import with participant predictions
- Automatic result sync with football-data.org
- Configurable scoring system
- Real-time dashboard with statistics
- General classification with phase filters
- Match view with predictions by player
- Top scorer and MVP statistics
- Responsive dark theme design
- HTMX dynamic interactions without page reload
- Cron job for automatic sync every hour (Docker)

## Technologies

- Django 6.x
- HTMX
- SQLite
- Pandas + openpyxl
- Tailwind CSS (CDN)
- uv (dependency management)
- Docker + Gunicorn

## Installation

### Local Development

#### 1. Clone repository

```bash
git clone <repository-url>
cd la-porrita
```

#### 2. Install dependencies

```bash
uv sync
```

#### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
FOOTBALL_DATA_TOKEN=your-football-data-token
```

#### 4. Run migrations

```bash
uv run python manage.py migrate
```

#### 5. Create superuser (optional)

```bash
uv run python manage.py createsuperuser
```

#### 6. Load demo data (optional)

```bash
uv run python manage.py seed_demo_data
```

#### 7. Start server

```bash
uv run python manage.py runserver
```

Application available at http://127.0.0.1:8000/

### Docker Deployment

#### 1. Build Docker image

```bash
docker build -t la-porrita .
```

#### 2. Run container

```bash
docker run -d \
  --name porrita \
  -p 8000:8000 \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e FOOTBALL_DATA_TOKEN=your-token \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  la-porrita
```

#### 3. Run migrations inside container

```bash
docker exec -it porrita .venv/bin/python manage.py migrate
```

#### 4. Create superuser inside container

```bash
docker exec -it porrita .venv/bin/python manage.py createsuperuser
```

The Docker image includes a cron job that automatically syncs football data and recalculates scores every hour.

## Management Commands

### Import pool Excel

```bash
uv run python manage.py import_pool_excel path/to/excel.xlsx
```

### Sync results with football-data.org

```bash
uv run python manage.py sync_football_data
```

### Recalculate scores

```bash
uv run python manage.py recalculate_scores
```

### Auto sync (for cron jobs)

```bash
uv run python manage.py auto_sync
```

### Load demo data

```bash
uv run python manage.py seed_demo_data
```

## Cron Job

The application includes a cron job that runs every hour to:
1. Sync match results from football-data.org
2. Recalculate all participant scores
3. Update rankings and standings

The cron job is configured in the Dockerfile and runs automatically when deployed with Docker.

To run manually:

```bash
uv run python manage.py auto_sync
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | `django-insecure-change-me-in-production` |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `FOOTBALL_DATA_TOKEN` | football-data.org API token | (empty) |
| `FOOTBALL_DATA_BASE_URL` | API base URL | `https://api.football-data.org/v4` |

## Project Structure

```
la-porrita/
├── manage.py
├── pyproject.toml
├── .env.example
├── README.md
├── Dockerfile
├── cronjob
├── porrita/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── pool/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── services/
│   │   ├── excel_importer.py
│   │   ├── football_api.py
│   │   └── scoring.py
│   ├── management/
│   │   └── commands/
│   │       ├── import_pool_excel.py
│   │       ├── sync_football_data.py
│   │       ├── recalculate_scores.py
│   │       ├── auto_sync.py
│   │       └── seed_demo_data.py
│   └── templates/
│       ├── base.html
│       └── pool/
│           ├── dashboard.html
│           ├── classification.html
│           ├── matches.html
│           ├── match_detail.html
│           ├── player_detail.html
│           ├── stats.html
│           └── partials/
│               ├── classification_table.html
│               ├── matches_list.html
│               └── predictions_list.html
└── templates/
    └── base.html
```

## football-data.org API

To use automatic result sync, you need a token from the football-data.org API.

1. Register at https://www.football-data.org/client/register
2. Get your authentication token
3. Add token to your `.env` file

## Scoring System

The scoring system is configurable and includes:

- **Group Stage**: Sign 2pts, Difference 1pt, Exact 2pts
- **Round of 16**: Sign 3pts, Exact 5pts
- **Quarter Finals**: Sign 5pts, Exact 9pts
- **Semi Finals**: Sign 10pts, Exact 15pts
- **Third Place**: Sign 15pts, Exact 30pts
- **Final**: Sign 25pts, Exact 40pts
- **Special Predictions**: Champion 50pts, Runner Up 25pts, etc.

## License

MIT
