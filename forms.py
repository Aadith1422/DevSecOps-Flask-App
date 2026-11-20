
import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField
from wtforms.validators import (
    DataRequired, Length, EqualTo, Email,
    NumberRange, ValidationError
)


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ]
    )

    submit = SubmitField("Register")

    def validate_password(self, field):
        password = field.data or ""

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Include an uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValidationError("Include a lowercase letter")

        if not re.search(r"\d", password):
            raise ValidationError("Include a number")

        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError("Include a special character")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")


class StudentForm(FlaskForm):
    name = StringField(
        "Student Name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)]
    )

    course = StringField(
        "Course",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    age = IntegerField(
        "Age",
        validators=[DataRequired(), NumberRange(min=1, max=120)]
    )

    submit = SubmitField("Save Student")
