
import os
from pathlib import Path
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, jsonify, render_template, redirect,
    url_for, flash, request, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError

from models import db, User, Student
from forms import RegistrationForm, LoginForm, StudentForm

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + str(Path(app.instance_path) / "students.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return func(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to DevSecOps Flask Application",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        if not 3 <= len(username) <= 80:
            form.username.errors.append("Invalid username length")
        elif User.query.filter_by(username=username).first():
            form.username.errors.append("Username already exists")
        elif User.query.filter_by(email=email).first():
            form.email.errors.append("Email already registered")
        else:
            user = User(
                username=username,
                email=email,
                role="user"
            )
            user.set_password(form.password.data)

            try:
                db.session.add(user)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Unable to register this account.", "danger")
            else:
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    student_count = Student.query.count()
    return render_template(
        "dashboard.html",
        student_count=student_count
    )


@app.route("/students")
@login_required
def students():
    records = Student.query.order_by(Student.id.desc()).all()
    return render_template(
        "students.html",
        students=records,
        form=StudentForm()
    )


@app.route("/students/add", methods=["POST"])
@admin_required
def add_student():
    form = StudentForm()

    if form.validate_on_submit():
        student = Student(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            course=form.course.data.strip(),
            age=form.age.data
        )

        try:
            db.session.add(student)
            db.session.commit()
            flash("Student added successfully.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Student email already exists.", "danger")
    else:
        flash("Invalid student details.", "danger")

    return redirect(url_for("students"))


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_student(student_id):
    student = db.get_or_404(Student, student_id)
    form = StudentForm(obj=student)

    if form.validate_on_submit():
        student.name = form.name.data.strip()
        student.email = form.email.data.strip().lower()
        student.course = form.course.data.strip()
        student.age = form.age.data

        try:
            db.session.commit()
            flash("Student updated successfully.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Student email already exists.", "danger")

        return redirect(url_for("students"))

    return render_template(
        "students.html",
        students=Student.query.order_by(Student.id.desc()).all(),
        form=StudentForm(),
        edit_form=form,
        editing_student=student
    )


@app.route("/students/<int:student_id>/delete", methods=["POST"])
@admin_required
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully.", "success")
    return redirect(url_for("students"))




if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
