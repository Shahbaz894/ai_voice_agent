uv venv --python 3.11
Using CPython 3.11.5
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate




import datetime
from  sqlalchemy import  Boolean,Column, DateTime,Integer,String, create_engine 
from sqlalchemy.orm import declarative_base,sessionmaker

DATABASE_URL="sqlite:///./appointments.db"

engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False})
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base=declarative_base()

class Appointment(Base):
    __tablename__="appointments"
    id=Column(Integer,primary_key=True,index=True)
    patient_name=Column(String,index=True)
    reason=Column(String,index=True)
    start_time=Column(DateTime,index=True)
    canceled=Column(Boolean,default=False)
    created_at=Column(DateTime,default=datetime.datetime.utcnow)
    
    
def init_db()-> None:
    Base.metadata.create_all(bind=engine)
    
    
init_db()
    






"""
FastAPI backend for Voice Medical Agent
Handles scheduling, canceling and listing patient appointments
"""

import datetime as dt
from typing import List

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from urllib3 import request

from database import SessionLocal, init_db, Appointment,get_db
from exception import (
    DatabaseConnectionError,
    AppointmentSaveError,
    ValidationError
)
from custom_logging import VoiceAgentLogger


# ============================================================
# INITIALIZATION
# ============================================================

logger = VoiceAgentLogger()

# Create tables on startup
init_db()

app = FastAPI(title="Voice Medical Appointment API")


# ============================================================
# PYDANTIC DATA CONTRACTS
# ============================================================

class AppointmentRequest(BaseModel):
    """
    Request model for scheduling appointment
    """
    patient_name: str
    reason: str
    start_time: dt.datetime


class AppointmentResponse(BaseModel):
    """
    Response model for appointment details
    """
    id: int
    patient_name: str
    reason: str
    start_time: dt.datetime
    canceled: bool
    created_at: dt.datetime


class CancelAppointmentRequest(BaseModel):
    """
    Request model for canceling appointment
    """
    patient_name: str
    date: dt.date


class CancelAppointmentResponse(BaseModel):
    """
    Response model after cancel operation
    """
    canceled_count: int


class ListAppointmentRequest(BaseModel):
    """
    Request model for listing appointments by date
    """
    date: dt.date


# ============================================================
# ENDPOINT: SCHEDULE APPOINTMENT
# ============================================================

@app.post("/schedule_appointment", response_model=AppointmentResponse)
def schedule_appointment(
    request: AppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a new patient appointment.

    Steps:
    1. Create Appointment object
    2. Add to DB session
    3. Commit transaction
    4. Refresh object to get generated ID
    5. Return response
    """

    try:
        new_appointment = Appointment(
            patient_name=request.patient_name,
            reason=request.reason,
            start_time=request.start_time
        )

        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)
        new_appointment_obj=AppointmentResponse(
            id=new_appointment.id,
            patient_name=new_appointment.patient_name,
            reason=new_appointment.reason,
            start_time=new_appointment.start_time,
            canceled=new_appointment.canceled,
            created_at=new_appointment.created_at
        )
       

        logger.info(
            f"Appointment scheduled for {request.patient_name} at {request.start_time}"
        )

        return new_appointment_obj

    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling appointment: {str(e)}")
        raise AppointmentSaveError(str(e))


# ============================================================
# ENDPOINT: CANCEL APPOINTMENT
# ============================================================

@app.post("/cancel_appointment", response_model=CancelAppointmentResponse)
def cancel_appointment(
    request: CancelAppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel all appointments for a patient on a given date.
    """

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
            raise ValidationError("No appointment found to cancel")

        for appointment in appointments:
            appointment.canceled = True

        db.commit()

        logger.info(
            f"Canceled {len(appointments)} appointment(s) for {request.patient_name}"
        )

        return CancelAppointmentResponse(
            canceled_count=len(appointments)
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error canceling appointment: {str(e)}")
        raise AppointmentSaveError(str(e))


# ============================================================
# ENDPOINT: LIST APPOINTMENTS
# ============================================================

@app.get("/list_appointments")
def list_appointments(
    date: dt.date,
    db: Session = Depends(get_db)
):
    """
    List all non-canceled appointments for a specific date.
    """

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
        book_appoinments=[]
        for appointment in result.scalars().all():
            appointment_obj=AppointmentResponse(
                id=appointment.id,
                patient_name=appointment.patient_name,
                reason=appointment.reason,
                start_time=appointment.start_time,
                canceled=appointment.canceled,
                created_at=appointment.created_at)
            book_appoinments.append(appointment_obj)

        logger.info(f"Listed appointments for date {date}")

        return book_appoinments

    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        raise DatabaseConnectionError(str(e))




import uvicorn
if __name__=="__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
    












    ///////////////////////////////////////////////////


    import streamlit as st
import datetime as dt
import requests


st.title("Patient Appointment Scheduler")

base_url = st.text_input(
    "Base URL",
    "http://127.0.0.1:8000"
).rstrip("/")

patient_name = st.text_input("Patient Name")
reason = st.text_input("Reason for Appointment")

# Streamlit datetime input already gives full datetime
start_datetime = st.datetime_input(
    "Start Time",
    value=dt.datetime.now() + dt.timedelta(days=1)
)

if st.button("Schedule Appointment"):

    payload = {
        "patient_name": patient_name,
        "reason": reason,
        "start_time": start_datetime.isoformat()
    }

    try:
        response = requests.post(
            f"{base_url}/schedule_appointment",
            json=payload
        )

        if response.status_code == 200:
            st.success("Appointment scheduled successfully!")
        else:
            st.error(f"Failed: {response.text}")

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
st.divider()


st.header("Cancel Appointment")


patient_name = st.text_input("Patient Name to Cancel",key="cancel_name")
cancel_date = st.date_input("Date to Cancel",key="cancel_date", value=dt.date.today())

if st.button("Cancel Appointment"):
    payload = {
        "patient_name": patient_name,
        "date": cancel_date.isoformat()
    }

    try:
        response = requests.post(
            f"{base_url}/cancel_appointment",
            json=payload
        )
        data=response.json()
        if response.status_code == 200:
            st.success(f"Appointment canceled successfully! Count: {data['canceled_count']}")
        else:
            st.error(f"Failed: {response.text}")

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        
        
        
        
        
appointments_date= st.date_input("Date to List Appointments",key="check_appointment_date", value=dt.date.today()  + dt.timedelta(days=1))
 
if st.button("List Appointments"):

    try:
        response = requests.get(
            f"{base_url}/list_appointments",
            params={"date": appointments_date.isoformat()}
        )

        if response.status_code == 200:
            data = response.json()
            st.success(f"Found {len(data)} appointments")

            for appointment in data:
                st.write(appointment)

        else:
            st.error(f"Failed: {response.text}")

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
