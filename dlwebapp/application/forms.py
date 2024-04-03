from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    IntegerField,
    SelectField,
    SubmitField,
    StringField,
    PasswordField,
    EmailField,
    RadioField,
    MultipleFileField,
)
from wtforms.validators import (
    Length,
    InputRequired,
    ValidationError,
    NumberRange,
    DataRequired,
    EqualTo,
    Email,
    Length,
    Optional,
)
from flask_wtf.file import FileField, FileAllowed, FileRequired

class SignUpForm(FlaskForm):
    email = EmailField(
        "Email", validators=[DataRequired(), Email(), Length(min=3, max=20)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=3, max=20)]
    )
    submit = SubmitField("Sign Up")


class SignInForm(FlaskForm):
    email = EmailField(
        "Email", validators=[DataRequired(), Email(), Length(min=3, max=20)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=3, max=20)]
    )
    submit = SubmitField("Sign In")

class PredictionForm(FlaskForm):
    model_choice = RadioField('Model Choice', choices=[('31x31', '31x31'), ('128x128', '128x128')], default='31x31')
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Predict')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[Optional(), Length(min=3, max=20)]
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            Optional(),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )
    submit_change = SubmitField("Change Password")
    submit_delete = SubmitField("Delete Account")

    def validate(self, **kwargs):
        if not super(ChangePasswordForm, self).validate(**kwargs):
            return False

        if self.submit_change.data:
            if not self.new_password.data or not self.confirm_password.data:
                self.new_password.errors.append("This field is required.")
                return False
            if len(self.new_password.data) < 3 or len(self.new_password.data) > 20:
                self.new_password.errors.append(
                    "Field must be between 3 and 20 characters long."
                )
                return False
            if self.new_password.data != self.confirm_password.data:
                self.confirm_password.errors.append("Passwords must match")
                return False

        return True


class BulkPredictionForm(FlaskForm):
    upload = FileField('Upload a file (zip only):', validators=[
        FileRequired(),
        FileAllowed(['zip'], 'Zip files only!')])
    model_choice = RadioField('Model Choice', choices=[
        ('31x31', '31x31'),
        ('128x128', '128x128')],
        default='31x31')
    submit = SubmitField('Bulk Predict')
