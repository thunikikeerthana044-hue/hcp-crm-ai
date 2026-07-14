"""
Run once after first setup to create a few demo HCPs so the Log Interaction
screen has someone to log against:

    python seed.py
"""
from app.database import SessionLocal, Base, engine
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

demo_hcps = [
    {"name": "Dr. Ananya Rao", "specialty": "Cardiology", "institution": "Apollo Hospitals",
     "email": "ananya.rao@example.com", "phone": "9876543210", "territory": "Hyderabad Central",
     "preferred_channel": "In-Person"},
    {"name": "Dr. Vikram Nair", "specialty": "Endocrinology", "institution": "KIMS Hospital",
     "email": "vikram.nair@example.com", "phone": "9876501234", "territory": "Hyderabad West",
     "preferred_channel": "Virtual"},
    {"name": "Dr. Sara Thomas", "specialty": "Oncology", "institution": "Yashoda Hospitals",
     "email": "sara.thomas@example.com", "phone": "9812345678", "territory": "Hyderabad South",
     "preferred_channel": "In-Person"},
]

for row in demo_hcps:
    exists = db.query(models.HCP).filter(models.HCP.name == row["name"]).first()
    if not exists:
        db.add(models.HCP(**row))

db.commit()
print(f"Seeded {len(demo_hcps)} demo HCPs (skipping any that already existed).")
db.close()
