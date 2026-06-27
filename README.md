# House Tracker

Track house viewing appointments with status, filters, and reminders. Built with Python Flet (MVVM), PostgreSQL, and uv.

## Quick Start (Web)

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/house_tracker"
uv run flet run main.py
```

App opens at `http://localhost:<port>`.

## Features

- Add, edit, and delete appointments (day, time, city, URL, description)
- Mark appointments as done or pending
- Filter by day and city
- Archive and recover appointments
- In-app notifications for upcoming appointments
- Open house listing URLs in browser

## Deploy API to Render

1. Create a **Web Service** from your Git repo
2. Add **PostgreSQL** and copy the Internal Database URL
3. Set environment variable `DATABASE_URL`
4. Build command: `pip install uv && uv sync`
5. Start command: `uv run uvicorn api.main:app --host 0.0.0.0 --port $PORT`

## Mobile App (Android APK)

1. Update `API_URL` in `mobile/main.py` to your Render API URL
2. Build the APK:

```bash
cd mobile
uv sync
uv run flet build apk
```

3. The APK will be in `mobile/build/apk/`

## Structure

```
main.py              # Web app entry (Flet + PostgreSQL)
api/main.py          # REST API backend (FastAPI + PostgreSQL)
mobile/main.py       # Mobile app (Flet + API client, no direct DB)
models/              # Appointment dataclass
viewmodels/          # MVVM viewmodels (appointments, archive)
views/               # Flet UI (appointments, archive)
services/            # PostgreSQL CRUD
```
