# Facial Recognition Attendance System — Backend

A Django REST API for the facial recognition attendance system. Handles all data storage, authentication, and attendance logic. Built as part of a three-part system alongside the frontend and facial recognition ML module.

## Live URL
[https://facial-recognition-attendance-backend-production.up.railway.app](https://facial-recognition-attendance-backend-production.up.railway.app)

---

## Tech Stack
- Python 3.13
- Django 6
- PostgreSQL (hosted on Railway)
- Deployed on Railway

---

## Project Structure

```
backend/              # Django project settings
api/                  # Login endpoint, mark-attendance endpoint
students/             # Student model and CRUD
professors/           # Professor model and CRUD
lectures/             # Course model and CRUD
timetable/            # TimetableEntry model and CRUD
enrollments/          # Enrollment model and CRUD
classrooms/           # Classroom model and CRUD
attendance/           # Attendance records
faces/                # Face encoding storage
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/login/` | Authenticate student or professor |
| GET/POST | `/api/students/` | List or create students |
| GET/POST | `/api/professors/` | List or create professors |
| GET/POST | `/api/classes/` | List or create courses |
| GET/POST | `/api/enrollments/` | List or create enrollments |
| GET/POST | `/api/timetable/` | List or build timetable |
| GET/POST | `/api/classrooms/` | List or create classrooms |
| GET/POST | `/api/reports/` | Attendance records |
| GET | `/api/student/<id>/attendance/` | Per-course attendance % for a student |
| POST | `/api/mark-attendance/` | Mark attendance (called by ML module) |
| DELETE | `/api/classes/<id>/` | Delete a course |
| DELETE | `/api/timetable/<id>/` | Delete a timetable entry |

### Mark Attendance Request Format
```json
POST /api/mark-attendance/
{
  "classroom": "301",
  "registration_number": "21BCE1234"
}
```

### Login Request Format
```json
POST /api/login/
{
  "id": "21BCE1234",
  "password": "21BCE1234"
}
```

---

## Getting Started Locally

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/advika-n/facial-recognition-attendance-backend.git
cd facial-recognition-attendance-backend
python -m venv env
.\env\Scripts\activate       # Windows
source env/bin/activate      # Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API will be running at [http://localhost:8000](http://localhost:8000).

> **Note:** Local development uses SQLite by default. The production deployment on Railway uses PostgreSQL.

---

## Database

Production uses a PostgreSQL database hosted on Railway. The connection is configured in `settings.py` under `DATABASES`. The database persists across deployments.

Migrations run automatically on every Railway deployment via the `Procfile`:
```
web: python manage.py migrate && gunicorn backend.wsgi --bind 0.0.0.0:$PORT
```

---

## CORS

The frontend Vercel URL is whitelisted in `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://attendance-frontend-eta-nine.vercel.app",
]
```

If the frontend URL changes, update this.

---

## Deployment

Railway auto-deploys on every push to the `main` branch of this repo.

---

## Related Repos
- [Frontend](https://github.com/advika-n/facial-recognition-attendance-frontend)
- ML Module (facial recognition) — separate repo, runs locally on camera device
