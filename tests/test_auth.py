from __future__ import annotations


class TestLogin:
    def test_login_success(self, client, admin_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "testpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, admin_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "ghost", "password": "whatever"},
        )
        assert response.status_code == 401


class TestGetMe:
    def test_get_me_authenticated(self, client, auth_headers, admin_user):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"

    def test_get_me_unauthenticated(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    def test_refresh_token_success(self, client, admin_user):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "testpassword"},
        )
        refresh_token = login_response.json()["refresh_token"]
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_token_invalid(self, client):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.token"},
        )
        assert response.status_code == 401
