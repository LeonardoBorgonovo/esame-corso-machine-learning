"""shared/errors.py — standard error response helpers.

All services use make_error() to build their error bodies, ensuring
the platform-standard format {"error": {"code": ..., "message": ..., "details": {...}}}.
"""
from __future__ import annotations
from flask import jsonify


def make_error(code: str, message: str, details: dict | None = None, status: int = 400):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


# ── Domain exceptions ─────────────────────────────────────────────────────────

class AppError(Exception):
    """Base class for all domain errors."""
    status_code: int = 400
    code: str = "ERROR"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_response(self):
        return make_error(self.code, self.message, self.details or None, self.status_code)


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class EmailAlreadyExistsError(ConflictError):
    code = "EMAIL_ALREADY_EXISTS"


class ReferenceNotFoundError(AppError):
    status_code = 422
    code = "REFERENCE_NOT_FOUND"


class DependencyUnavailableError(AppError):
    status_code = 503
    code = "DEPENDENCY_UNAVAILABLE"


class InvalidStatusTransitionError(AppError):
    status_code = 422
    code = "INVALID_STATUS_TRANSITION"
