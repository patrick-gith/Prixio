from django import forms
from django.utils.translation import gettext_lazy as _


class SearchForm(forms.Form):
    identifier = forms.CharField(
        max_length=255,
        label="",
        widget=forms.TextInput(attrs={
            "class": "form-input search-input",
            "placeholder": _("ISBN, code-barres, Bitcoin, Ethereum…"),
            "autofocus": True,
            "autocomplete": "off",
        }),
    )
