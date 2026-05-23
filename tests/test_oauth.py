from __future__ import annotations

import base64
import hashlib
import secrets

import pytest

from app.models.oauth import OAuthClient
from app.models.respondent import Respondent
from app.services.oauth_service import hash_pin, verify_pkce_challenge


@pytest.fixture
def oauth_client(db):
    client = OAuthClient(
        client_id="test-client-id",
        client_name="TimeStudy Android",
        redirect_uris="com.example.timestudy://callback",
        scope="sync",
        grant_types="authorization_code refresh_token",
        response_types="code",
        is_active=True,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture
def respondent_with_pin(db):
    resp = Respondent(
        resp_id="R-AUTH",
        name="Auth Test",
        is_active=True,
        pin_hash=hash_pin("1234"),
    )
    db.add(resp)
    db.commit()
    db.refresh(resp)
    return resp


def make_pkce() -> tuple[str, str]:
    """Generate a PKCE (code_verifier, code_challenge) pair."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


class TestPkceVerification:
    def test_valid_pkce_pair(self):
        verifier, challenge = make_pkce()
        assert verify_pkce_challenge(verifier, challenge, "S256") is True

    def test_wrong_verifier(self):
        _, challenge = make_pkce()
        assert verify_pkce_challenge("wrongverifier", challenge, "S256") is False

    def test_unsupported_method(self):
        verifier, challenge = make_pkce()
        assert verify_pkce_challenge(verifier, challenge, "plain") is False


class TestOAuthClientManagement:
    def test_list_clients_requires_auth(self, client):
        response = client.get("/api/v1/oauth/clients")
        assert response.status_code == 401

    def test_list_clients_authenticated(self, client, auth_headers, oauth_client):
        response = client.get("/api/v1/oauth/clients", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_create_client(self, client, auth_headers):
        response = client.post(
            "/api/v1/oauth/clients",
            json={
                "client_name": "New App",
                "redirect_uris": "myapp://callback",
                "scope": "sync",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["client_name"] == "New App"
        assert "client_id" in data

    def test_get_client(self, client, auth_headers, oauth_client):
        response = client.get(
            f"/api/v1/oauth/clients/{oauth_client.client_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["client_name"] == "TimeStudy Android"

    def test_update_client(self, client, auth_headers, oauth_client):
        response = client.patch(
            f"/api/v1/oauth/clients/{oauth_client.client_id}",
            json={"client_name": "Updated App"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["client_name"] == "Updated App"

    def test_delete_client(self, client, auth_headers, oauth_client):
        response = client.delete(
            f"/api/v1/oauth/clients/{oauth_client.client_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204


class TestOAuthAuthorize:
    def test_get_authorize_shows_login_page(
        self, client, oauth_client, respondent_with_pin
    ):
        _, challenge = make_pkce()
        response = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": "test-client-id",
                "redirect_uri": "com.example.timestudy://callback",
                "scope": "sync",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "TimeStudy" in response.text

    def test_get_authorize_unknown_client(self, client):
        _, challenge = make_pkce()
        response = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": "unknown",
                "redirect_uri": "myapp://callback",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == 400

    def test_post_authorize_valid_credentials_redirects(
        self, client, oauth_client, respondent_with_pin
    ):
        verifier, challenge = make_pkce()
        response = client.post(
            "/oauth/authorize",
            data={
                "client_id": "test-client-id",
                "redirect_uri": "com.example.timestudy://callback",
                "scope": "sync",
                "state": "xyz",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resp_id": "R-AUTH",
                "pin": "1234",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        location = response.headers["location"]
        assert "code=" in location

    def test_post_authorize_invalid_pin_shows_error(
        self, client, oauth_client, respondent_with_pin
    ):
        _, challenge = make_pkce()
        response = client.post(
            "/oauth/authorize",
            data={
                "client_id": "test-client-id",
                "redirect_uri": "com.example.timestudy://callback",
                "scope": "sync",
                "state": "",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resp_id": "R-AUTH",
                "pin": "wrongpin",
            },
        )
        assert response.status_code == 200
        assert "tidak valid" in response.text


class TestOAuthTokenExchange:
    def _get_auth_code(self, client, oauth_client, respondent_with_pin):
        verifier, challenge = make_pkce()
        response = client.post(
            "/oauth/authorize",
            data={
                "client_id": "test-client-id",
                "redirect_uri": "com.example.timestudy://callback",
                "scope": "sync",
                "state": "",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resp_id": "R-AUTH",
                "pin": "1234",
            },
            follow_redirects=False,
        )
        location = response.headers["location"]
        code = dict(p.split("=") for p in location.split("?")[1].split("&"))["code"]
        return code, verifier

    def test_exchange_code_for_token(self, client, oauth_client, respondent_with_pin):
        code, verifier = self._get_auth_code(client, oauth_client, respondent_with_pin)
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "test-client-id",
                "code": code,
                "redirect_uri": "com.example.timestudy://callback",
                "code_verifier": verifier,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_exchange_wrong_verifier(self, client, oauth_client, respondent_with_pin):
        code, _ = self._get_auth_code(client, oauth_client, respondent_with_pin)
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "test-client-id",
                "code": code,
                "redirect_uri": "com.example.timestudy://callback",
                "code_verifier": "wrongverifier",
            },
        )
        assert response.status_code == 400

    def test_refresh_token(self, client, oauth_client, respondent_with_pin):
        code, verifier = self._get_auth_code(client, oauth_client, respondent_with_pin)
        token_response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "test-client-id",
                "code": code,
                "redirect_uri": "com.example.timestudy://callback",
                "code_verifier": verifier,
            },
        )
        refresh_token = token_response.json()["refresh_token"]
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": "test-client-id",
                "refresh_token": refresh_token,
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
