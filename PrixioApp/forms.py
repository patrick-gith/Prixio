# PrixioApp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_("Adresse e-mail"),
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "vous@exemple.com",
            "autocomplete": "email",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("username", "password1", "password2"):
            self.fields[field_name].widget.attrs.update({
                "class": "form-input",
                "autocomplete": "off",
            })
        self.fields["username"].widget.attrs["placeholder"] = "votre_pseudo"
        self.fields["password1"].widget.attrs["placeholder"] = "••••••••"
        self.fields["password2"].widget.attrs["placeholder"] = "••••••••"