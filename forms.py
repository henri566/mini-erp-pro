from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
  username = StringField('Nom d’utilisateur', validators=[DataRequired()])
  password = PasswordField('Mot de passe', validators=[DataRequired()])
  submit = SubmitField('Se connecter')


class UserRegisterForm(FlaskForm):
  username = StringField(
      'Nom d’utilisateur', validators=[DataRequired(), Length(min=3, max=50)]
  )
  password = PasswordField(
      'Mot de passe', validators=[DataRequired(), Length(min=6)]
  )
  submit = SubmitField('Créer le compte')