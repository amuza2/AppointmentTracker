# House Tracker

Track house viewing appointments with status, filters, and reminders. Built with Python Flet (MVVM), PostgreSQL, and uv.

## Quick Start

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

## Deploy

**Render**: Add PostgreSQL, set `DATABASE_URL`, and use:

```bash
uv run flet run main.py --port $PORT
```

## Structure

```
main.py              # Entry, navigation, notifications
models/              # Appointment dataclass
viewmodels/          # MVVM viewmodels (appointments, archive)
views/               # Flet UI (appointments, archive)
services/            # PostgreSQL CRUD
```
