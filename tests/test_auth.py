from models import db, User


def test_home(client):
    assert client.get("/").status_code == 200


def test_health(client):
    assert client.get("/health").status_code == 200


def test_registration_page(client):
    assert client.get("/register").status_code == 200


def test_login_page(client):
    assert client.get("/login").status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_registration(client):
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    user = User.query.filter_by(
        username="testuser"
    ).first()

    assert user is not None
    assert user.check_password("StrongPass123!")


def test_duplicate_registration(client):
    user = User(
        username="testuser",
        email="testuser@example.com"
    )
    user.set_password("StrongPass123!")

    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "another@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        },
        follow_redirects=True
    )

    assert b"Username already exists" in response.data


def test_invalid_login(client):
    response = client.post(
        "/login",
        data={
            "email": "unknown@example.com",
            "password": "WrongPassword123!"
        },
        follow_redirects=True
    )

    assert b"Invalid email or password" in response.data