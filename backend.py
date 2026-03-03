"""
FastAPI backend for Voice Medical Agent
Handles scheduling, canceling and listing patient appointments
"""

import datetime as dt
from typing import List

from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal, init_db, Appointment, get_db
from exception import (
    DatabaseConnectionError,
    AppointmentSaveError,
    ValidationError,
    VoiceAgentException
)
from custom_logging import VoiceAgentLogger

# ============================================================
# INITIALIZATION
# ============================================================

logger = VoiceAgentLogger()
init_db()  # Create tables on startup
app = FastAPI(title="Voice Medical Appointment API")


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(VoiceAgentException)
async def voice_agent_exception_handler(request: Request, exc: VoiceAgentException):
    """Return JSON response for custom exceptions"""
    return JSONResponse(
        status_code=getattr(exc, "http_status", 400),
        content=exc.to_dict()
    )


# ============================================================
# PYDANTIC DATA CONTRACTS
# ============================================================

class AppointmentRequest(BaseModel):
    patient_name: str
    reason: str
    start_time: dt.datetime


class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    reason: str
    start_time: dt.datetime
    canceled: bool
    created_at: dt.datetime


class CancelAppointmentRequest(BaseModel):
    patient_name: str
    date: dt.date


class CancelAppointmentResponse(BaseModel):
    canceled_count: int


class ListAppointmentRequest(BaseModel):
    date: dt.date


# ============================================================
# ENDPOINT: SCHEDULE APPOINTMENT
# ============================================================

@app.post("/schedule_appointment", response_model=AppointmentResponse)
def schedule_appointment(request: AppointmentRequest, db: Session = Depends(get_db)):
    try:
        new_appointment = Appointment(
            patient_name=request.patient_name,
            reason=request.reason,
            start_time=request.start_time
        )
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        new_appointment_obj = AppointmentResponse(
            id=new_appointment.id,
            patient_name=new_appointment.patient_name,
            reason=new_appointment.reason,
            start_time=new_appointment.start_time,
            canceled=new_appointment.canceled,
            created_at=new_appointment.created_at
        )

        logger.info(f"Appointment scheduled for {request.patient_name} at {request.start_time}")
        return new_appointment_obj

    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling appointment: {str(e)}")
        raise AppointmentSaveError(str(e))


# ============================================================
# ENDPOINT: CANCEL APPOINTMENT
# ============================================================

from fastapi import HTTPException

@app.post("/cancel_appointment", response_model=CancelAppointmentResponse)
def cancel_appointment(request: CancelAppointmentRequest, db: Session = Depends(get_db)):
    try:
        start_dt = dt.datetime.combine(request.date, dt.time.min)
        end_dt = dt.datetime.combine(request.date, dt.time.max)

        result = db.execute(
            select(Appointment)
            .where(Appointment.patient_name == request.patient_name)
            .where(Appointment.start_time >= start_dt)
            .where(Appointment.start_time <= end_dt)
            .where(Appointment.canceled == False)
        )

        appointments = result.scalars().all()

        if not appointments:
            # Proper HTTP error for client
            raise ValidationError("No appointment found to cancel")

        for appointment in appointments:
            appointment.canceled = True

        db.commit()
        logger.info(f"Canceled {len(appointments)} appointment(s) for {request.patient_name}")
        return CancelAppointmentResponse(canceled_count=len(appointments))

    except ValidationError as ve:
        # Return 400 error with proper message
        db.rollback()
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=ve.to_dict())

    except Exception as e:
        # Only real DB errors reach here
        db.rollback()
        logger.error(f"Error canceling appointment: {str(e)}")
        raise AppointmentSaveError(str(e))



# ============================================================
# ENDPOINT: LIST APPOINTMENTS
# ============================================================

@app.get("/list_appointments", response_model=List[AppointmentResponse])
def list_appointments(date: dt.date, db: Session = Depends(get_db)):
    try:
        start_dt = dt.datetime.combine(date, dt.time.min)
        end_dt = dt.datetime.combine(date, dt.time.max)

        result = db.execute(
            select(Appointment)
            .where(Appointment.canceled == False)
            .where(Appointment.start_time >= start_dt)
            .where(Appointment.start_time <= end_dt)
            .order_by(Appointment.start_time.asc())
        )

        book_appointments = []
        for appointment in result.scalars().all():
            appointment_obj = AppointmentResponse(
                id=appointment.id,
                patient_name=appointment.patient_name,
                reason=appointment.reason,
                start_time=appointment.start_time,
                canceled=appointment.canceled,
                created_at=appointment.created_at
            )
            book_appointments.append(appointment_obj)

        logger.info(f"Listed appointments for date {date}")
        return book_appointments

    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        raise DatabaseConnectionError(str(e))


# ============================================================
# RUN SERVER
# ============================================================

import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
