import streamlit as st
import datetime as dt
import requests

st.title("Patient Appointment Scheduler")

# -------------------------
# Base URL input
# -------------------------
base_url = st.text_input(
    "Base URL",
    "http://127.0.0.1:8000"
).rstrip("/")


# -------------------------
# Schedule Appointment
# -------------------------
st.header("Schedule Appointment")

schedule_patient_name = st.text_input("Patient Name", key="schedule_name")
reason = st.text_input("Reason for Appointment", key="reason")

start_datetime = st.datetime_input(
    "Start Time",
    value=dt.datetime.now() + dt.timedelta(days=1),
    key="start_datetime"
)

if st.button("Schedule Appointment"):
    payload = {
        "patient_name": schedule_patient_name,
        "reason": reason,
        "start_time": start_datetime.isoformat()
    }

    try:
        response = requests.post(f"{base_url}/schedule_appointment", json=payload)

        if response.status_code == 200:
            st.success("Appointment scheduled successfully!")
        else:
            # Handle custom exception JSON from backend
            try:
                error_data = response.json()
                st.error(f"{error_data.get('error_code')}: {error_data.get('message')}")
            except Exception:
                st.error(f"Failed: {response.text}")

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")


st.divider()


# -------------------------
# Cancel Appointment
# -------------------------
st.header("Cancel Appointment")

# Input for patient name to cancel
cancel_patient_name = st.text_input(
    "Patient Name to Cancel", 
    key="cancel_name"
)

# Date input for canceling — default to tomorrow (same as schedule default)
cancel_date = st.date_input(
    "Date to Cancel", 
    key="cancel_date", 
    value=dt.date.today() + dt.timedelta(days=1)  # match schedule appointment default
)

if st.button("Cancel Appointment", key="cancel_button"):
    payload = {
        "patient_name": cancel_patient_name,
        "date": cancel_date.isoformat()
    }

    try:
        response = requests.post(
            f"{base_url}/cancel_appointment", 
            json=payload
        )

        # Handle success
        if response.status_code == 200:
            data = response.json()
            st.success(f"Appointment canceled successfully! Count: {data.get('canceled_count')}")
        else:
            # Handle backend custom exceptions
            try:
                error_data = response.json()
                st.error(f"{error_data.get('error_code')}: {error_data.get('message')}")
            except Exception:
                st.error(f"Failed: {response.text}")

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")

st.divider()


# -------------------------
# List Appointments
# -------------------------
st.header("List Appointments")

appointments_date = st.date_input(
    "Date to List Appointments",
    key="check_appointment_date",
    value=dt.date.today() + dt.timedelta(days=1)
)

if st.button("List Appointments", key="list_button"):
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
            try:
                error_data = response.json()
                st.error(f"{error_data.get('error_code')}: {error_data.get('message')}")
            except Exception:
                st.error(f"Failed: {response.text}")

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
