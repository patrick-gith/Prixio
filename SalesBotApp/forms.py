from django import forms

from .models import ChannelPolicy, SearchQuery, Service, TestScenario


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "slug", "url_comeup", "description",
                  "keywords_fr", "keywords_en", "category", "price", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "keywords_fr": forms.Textarea(attrs={"rows": 2}),
            "keywords_en": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-checkbox")
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-input")
            else:
                field.widget.attrs.setdefault("class", "form-input")


class PlaygroundForm(forms.Form):
    text = forms.CharField(
        label="Décrivez le besoin du prospect",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "class": "form-input",
            "placeholder": "Ex : Je veux automatiser les réponses WhatsApp de mes clients.",
        }),
    )
    language_override = forms.ChoiceField(
        choices=[("", "Auto"), ("fr", "Français"), ("en", "English")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    service_override = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        required=False,
        empty_label="Auto (matching auto)",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class SearchQueryForm(forms.ModelForm):
    class Meta:
        model = SearchQuery
        fields = ["kind", "query", "url", "channel", "is_active"]


class ChannelPolicyForm(forms.ModelForm):
    class Meta:
        model = ChannelPolicy
        fields = ["is_enabled", "mode", "min_score", "daily_limit", "require_human"]


class TestScenarioForm(forms.ModelForm):
    class Meta:
        model = TestScenario
        fields = ["name", "text", "expected_service"]


class CSVImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={"class": "form-input", "accept": ".csv"}),
    )
    activate = forms.BooleanField(
        required=False, initial=False,
        label="Activer les services après import",
    )
