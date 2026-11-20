from models import db, User, Student


def create_user(username, email, role):
    user = User(username=username, email=email, role=role)
    user.set_password("StrongPass123!")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": "StrongPass123!"
        },
        follow_redirects=True
    )


def test_regular_user_cannot_add_student(client):
    create_user("studentuser", "student@example.com", "user")
    login(client, "student@example.com")

    response = client.post(
        "/students/add",
        data={
            "name": "Rahul",
            "email": "rahul@example.com",
            "course": "Cybersecurity",
            "age": 22
        }
    )

    assert response.status_code == 403


def test_admin_can_add_student(client):
    create_user("admin", "admin@example.com", "admin")
    login(client, "admin@example.com")

    response = client.post(
        "/students/add",
        data={
            "name": "Rahul",
            "email": "rahul@example.com",
            "course": "Cybersecurity",
            "age": 22
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert Student.query.filter_by(
        email="rahul@example.com"
    ).first() is not None


def test_admin_can_delete_student(client):
    create_user("admin", "admin@example.com", "admin")

    student = Student(
        name="Rahul",
        email="rahul@example.com",
        course="Cybersecurity",
        age=22
    )
    db.session.add(student)
    db.session.commit()
    student_id = student.id

    login(client, "admin@example.com")

    response = client.post(
        f"/students/{student_id}/delete",
        follow_redirects=True
    )

    assert response.status_code == 200
    assert db.session.get(Student, student_id) is None


def test_regular_user_cannot_delete_student(client):
    create_user("studentuser", "student@example.com", "user")

    student = Student(
        name="Rahul",
        email="rahul@example.com",
        course="Cybersecurity",
        age=22
    )
    db.session.add(student)
    db.session.commit()

    login(client, "student@example.com")

    response = client.post(
        f"/students/{student.id}/delete"
    )

    assert response.status_code == 403