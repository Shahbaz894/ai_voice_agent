# exception.py
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import Request

class VoiceAgentException(Exception):
    """
    Base Exception for Voice Medical Agent
    Includes error code, message, timestamp, and optional HTTP status
    """

    def __init__(self, message: str, error_code: str = "VOICE_AGENT_ERROR", http_status: int = 400):
        self.message = message
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
        self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self):
        """Return exception details as a dictionary"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


# ============================
# Specific Exceptions
# ============================

class DatabaseConnectionError(VoiceAgentException):
    """Raised when database connection fails"""
    def __init__(self, message="Database connection failed"):
        super().__init__(message, error_code="DB_CONNECTION_ERROR", http_status=500)


class AppointmentSaveError(VoiceAgentException):
    """Raised when appointment saving fails"""
    def __init__(self, message="Failed to save appointment"):
        super().__init__(message, error_code="APPOINTMENT_SAVE_ERROR", http_status=500)


class ValidationError(VoiceAgentException):
    """Raised when input validation fails"""
    def __init__(self, message="Invalid input data"):
        super().__init__(message, error_code="VALIDATION_ERROR", http_status=400)


# ============================
# FastAPI Exception Handler
# ============================

async def voice_agent_exception_handler(request: Request, exc: VoiceAgentException):
    """
    Handles all VoiceAgentException and returns JSON response
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )
