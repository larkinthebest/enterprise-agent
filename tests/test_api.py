"""Integration tests for API endpoints."""

import pytest


def test_health_endpoint(client):
    """Health endpoint should return even if infrastructure is down."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "postgres" in data


def test_auth_whoami_no_key(client):
    """Missing API key should return 422."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 422


def test_auth_whoami_bad_key(client):
    """Invalid API key should return 401."""
    resp = client.get("/api/v1/auth/me", headers={"X-Api-Key": "bad"})
    assert resp.status_code == 401


def test_auth_whoami_success(client, admin_user):
    user, api_key = admin_user
    resp = client.get("/api/v1/auth/me", headers={"X-Api-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"].startswith("testadmin")
    assert data["role"] == "admin"


def test_create_user_requires_admin(client, operator_user):
    _, api_key = operator_user
    resp = client.post(
        "/api/v1/auth/users",
        headers={"X-Api-Key": api_key},
        json={"username": "newuser"},
    )
    assert resp.status_code == 403


def test_create_user_as_admin(client, admin_user):
    _, api_key = admin_user
    resp = client.post(
        "/api/v1/auth/users",
        headers={"X-Api-Key": api_key},
        json={"username": "newuser_test_create", "role": "viewer"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser_test_create"
    assert data["api_key"] is not None


def test_list_users_admin(client, admin_user):
    _, api_key = admin_user
    resp = client.get("/api/v1/auth/users", headers={"X-Api-Key": api_key})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_agent_run_requires_auth(client):
    """Agent endpoint should reject unauthenticated requests."""
    resp = client.post("/api/v1/agent/run", json={"request_text": "hello"})
    assert resp.status_code == 422  # missing header


def test_audit_logs_requires_admin(client, operator_user):
    _, api_key = operator_user
    resp = client.get("/api/v1/audit/logs", headers={"X-Api-Key": api_key})
    assert resp.status_code == 403
