from __future__ import annotations

import pytest

from app.models.respondent import Respondent
from app.services.oauth_service import hash_pin


@pytest.fixture
def sample_respondent(db):
    resp = Respondent(
        resp_id="R-001",
        name="Budi Santoso",
        email="budi@example.com",
        department="Engineering",
        is_active=True,
        pin_hash=hash_pin("1234"),
    )
    db.add(resp)
    db.commit()
    db.refresh(resp)
    return resp


class TestListRespondents:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/respondents")
        assert response.status_code == 401

    def test_list_empty(self, client, auth_headers):
        response = client.get("/api/v1/respondents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_with_respondent(self, client, auth_headers, sample_respondent):
        response = client.get("/api/v1/respondents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["resp_id"] == "R-001"

    def test_search_by_name(self, client, auth_headers, sample_respondent):
        response = client.get("/api/v1/respondents?search=Budi", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_search_no_match(self, client, auth_headers, sample_respondent):
        response = client.get("/api/v1/respondents?search=ZZZNOMATCH", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestCreateRespondent:
    def test_create_success(self, client, auth_headers):
        response = client.post(
            "/api/v1/respondents",
            json={
                "resp_id": "R-002",
                "name": "Siti Rahayu",
                "email": "siti@example.com",
                "pin": "5678",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["resp_id"] == "R-002"
        assert data["name"] == "Siti Rahayu"

    def test_create_duplicate_resp_id(self, client, auth_headers, sample_respondent):
        response = client.post(
            "/api/v1/respondents",
            json={"resp_id": "R-001", "name": "Duplicate"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_create_invalid_resp_id(self, client, auth_headers):
        response = client.post(
            "/api/v1/respondents",
            json={"resp_id": "invalid resp!", "name": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetRespondent:
    def test_get_existing(self, client, auth_headers, sample_respondent):
        response = client.get("/api/v1/respondents/R-001", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["resp_id"] == "R-001"

    def test_get_not_found(self, client, auth_headers):
        response = client.get("/api/v1/respondents/R-999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateRespondent:
    def test_update_name(self, client, auth_headers, sample_respondent):
        response = client.patch(
            "/api/v1/respondents/R-001",
            json={"name": "Budi Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Budi Updated"

    def test_update_pin(self, client, auth_headers, sample_respondent):
        response = client.patch(
            "/api/v1/respondents/R-001",
            json={"pin": "9999"},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestDeleteRespondent:
    def test_delete_success(self, client, auth_headers, sample_respondent):
        response = client.delete("/api/v1/respondents/R-001", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_not_found(self, client, auth_headers):
        response = client.delete("/api/v1/respondents/R-999", headers=auth_headers)
        assert response.status_code == 404
