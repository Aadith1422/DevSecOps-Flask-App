def test_login_rejects_missing_csrf(client):
    from app import app

    app.config["WTF_CSRF_ENABLED"] = True

    try:
        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
    finally:
        app.config["WTF_CSRF_ENABLED"] = False


def test_registration_rejects_missing_csrf(client):
    from app import app

    app.config["WTF_CSRF_ENABLED"] = True

    try:
        response = client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!"
            }
        )

        assert response.status_code == 400
    finally:
        app.config["WTF_CSRF_ENABLED"] = False