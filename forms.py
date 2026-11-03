from flask import session
from flask_wtf import FlaskForm
from markupsafe import escape
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from translations import TRADUCTIONS


class Traduit:
    """Texte traduit AU MOMENT DE L'AFFICHAGE, dans la langue de la session (FR ou EN).

    Les libellés d'un formulaire sont définis une seule fois au démarrage de l'application :
    un simple texte resterait donc figé dans une seule langue.
    """

    def __init__(self, cle, **valeurs):
        self.cle = cle
        self.valeurs = valeurs

    def _texte(self):
        lang = session.get('lang', 'fr')
        lang = lang if lang in TRADUCTIONS else 'fr'
        texte = TRADUCTIONS[lang].get(self.cle) or TRADUCTIONS['fr'].get(self.cle, self.cle)
        return texte.format(**self.valeurs) if self.valeurs else texte

    def __str__(self):
        return self._texte()

    def __html__(self):
        return str(escape(self._texte()))


class LoginForm(FlaskForm):
    username = StringField(Traduit('form.username'),
                           validators=[DataRequired(message=Traduit('form.required'))])
    password = PasswordField(Traduit('form.password'),
                             validators=[DataRequired(message=Traduit('form.required'))])
    submit = SubmitField(Traduit('form.login'))


class UserRegisterForm(FlaskForm):
    username = StringField(
        Traduit('form.username'),
        validators=[DataRequired(message=Traduit('form.required')),
                    Length(min=3, max=50, message=Traduit('form.min_username'))]
    )
    password = PasswordField(
        Traduit('form.password'),
        validators=[DataRequired(message=Traduit('form.required')),
                    Length(min=6, message=Traduit('form.min_password'))]
    )
    submit = SubmitField(Traduit('form.register'))