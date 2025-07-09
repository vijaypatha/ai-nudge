# File: backend/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

def test_verify_otp_fails_missing_phone(client: TestClient):
    """
    Tests that the OTP verification endpoint fails if the phone number is missing.
    """
    # Arrange: Payload is missing the 'phone_number' field
    payload = {"otp_code": "123456"}

    # Act
    response = client.post("/api/auth/otp/verify", json=payload)

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["type"] == "missing"
    assert data["detail"][0]["loc"] == ["body", "phone_number"]

def test_verify_otp_fails_missing_code(client: TestClient):
    """
    Tests that the OTP verification endpoint fails if the OTP code is missing.
    """
    # Arrange: Payload is missing the 'otp_code' field
    payload = {"phone_number": "+15551234567"}

    # Act
    response = client.post("/api/auth/otp/verify", json=payload)

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["type"] == "missing"
    assert data["detail"][0]["loc"] == ["body", "otp_code"]
