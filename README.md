# AIMS Senegal Thesis Defense Portal

A full Django application for managing and evaluating thesis defenses at AIMS Senegal.

## Quick Start

### 1. Install dependencies
```bash
pip install django openpyxl python-docx Pillow reportlab
```

### 2. Set up database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Create initial site password
```bash
python manage.py shell -c "
from defense.models import SitePassword
SitePassword.objects.get_or_create(id=1, defaults={'password': 'aimssn'})
"
```

### 4. Run development server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Default Credentials
- **Platform password**: `aimssn` (changeable via Django admin)
- **Admin login**: Create via `createsuperuser`
- **Admin URL**: http://127.0.0.1:8000/admin/

## User Flow
1. `/` — Animated landing page with draggable AIMS logo
2. `/login/` — Password gate (default: `aimssn`)
3. `/sessions/` — List of defense sessions; import Excel files here
4. `/sessions/<id>/` — Two rooms (AIMS Room 1, AIMS Room 2)
5. `/sessions/<id>/room/<1or2>/` — Student table with Start/Done/Link/Copy/PV buttons
6. `/defense/<token>/` — Public link for evaluators (active only while defense is ongoing)
7. `/defense/<token>/panel/` — Clickable grid of panel members
8. `/defense/<token>/eval/<index>/` — Evaluation form per member
9. `/student/<id>/pv/` — PV overview with download buttons (Word, PDF, ZIP)

## Excel Import Format
Columns expected (from AIMS Coop schedule):
- Time (GMT), Surname, Given Names, Research Project title
- Room, Date, Academic Supervisors, Email of Supervisor, Institution of Supervisors
- Academic Supervisors 2, Email of Supervisor 2
- President Jury, Email, Affiliation
- Examiner 1, Examiner 1 email, Affiliation
- Examiner 2, Examiner 2 email, Affiliation

## Admin Actions
- Change site password: Admin → Site Password
- Reset a defense start: Admin → Students → select → "Reset defense start"
- Create/delete sessions: Admin → Sessions

## Setup Note (v2)
Default password remains **`aimssn`** — auto-seeded via migration `0003_seed_site_password`.
Run `python manage.py migrate` on a fresh database and the password will be set automatically.
Change it anytime via Admin → Site Password.
