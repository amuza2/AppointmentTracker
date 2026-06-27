import os
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services import database
from models.appointment import Appointment

app = FastAPI(title="House Tracker API")


class AppointmentCreate(BaseModel):
    day: str
    time: str
    city: str
    url: str
    description: str = ""


class AppointmentUpdate(BaseModel):
    day: str
    time: str
    city: str
    url: str
    description: str = ""
    status: str = "pending"


class StatusUpdate(BaseModel):
    status: str


@app.on_event("startup")
def startup():
    database.init_db()


@app.get("/api/appointments")
def get_active():
    return [asdict(a) for a in database.get_active_appointments()]


@app.get("/api/appointments/archived")
def get_archived():
    return [asdict(a) for a in database.get_archived_appointments()]


@app.get("/api/appointments/upcoming")
def get_upcoming():
    return [asdict(a) for a in database.get_upcoming_appointments()]


@app.post("/api/appointments")
def create_appointment(body: AppointmentCreate):
    apt = database.insert_appointment(body.day, body.time, body.city, body.url, body.description)
    return asdict(apt)


@app.put("/api/appointments/{appointment_id}")
def update_appointment(appointment_id: int, body: AppointmentUpdate):
    database.update_appointment(appointment_id, body.day, body.time, body.city, body.url, body.description)
    database.update_appointment_status(appointment_id, body.status)
    return {"ok": True}


@app.put("/api/appointments/{appointment_id}/status")
def update_status(appointment_id: int, body: StatusUpdate):
    database.update_appointment_status(appointment_id, body.status)
    return {"ok": True}


@app.put("/api/appointments/{appointment_id}/archive")
def archive_appointment(appointment_id: int):
    database.archive_appointment(appointment_id)
    return {"ok": True}


@app.put("/api/appointments/{appointment_id}/unarchive")
def unarchive_appointment(appointment_id: int):
    database.unarchive_appointment(appointment_id)
    return {"ok": True}


@app.delete("/api/appointments/{appointment_id}")
def delete_appointment(appointment_id: int):
    database.delete_appointment(appointment_id)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
