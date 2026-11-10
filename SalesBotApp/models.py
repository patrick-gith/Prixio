from django.db import models


class Service(models.Model):
    CATEGORY_CHOICES = [
        ("automation", "Automatisation, IA et développement logiciel"),
        ("billing", "Facturation, comptabilité et gestion"),
        ("marketing", "Marketing digital, SEO et acquisition"),
        ("communication", "Communication, vente et paiement"),
        ("apps", "Applications métier et solutions spécialisées"),
    ]
    title       = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=500)
    url_comeup  = models.URLField()
    description = models.TextField(blank=True)
    keywords_fr = models.TextField(blank=True)
    keywords_en = models.TextField(blank=True)
    category    = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="automation")
    price       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active   = models.BooleanField(default=False)
    embedding   = models.JSONField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return self.title

    @property
    def category_label(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)


class Opportunity(models.Model):
    SOURCE_CHOICES = [
        ("telegram", "Telegram"), ("discord", "Discord"),
        ("quora", "Quora"), ("reddit", "Reddit"),
        ("google_alerts", "Google Alerts"), ("brave", "Brave Search"),
        ("rss", "RSS"), ("manual", "Manuel"),
    ]
    STATUS_CHOICES = [
        ("new", "Nouveau"), ("analysed", "Analysé"),
        ("recommended", "Recommandé"), ("drafted", "Brouillon"),
        ("published", "Publié"), ("skipped", "Ignoré"), ("rejected", "Rejeté"),
    ]
    source      = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    channel     = models.CharField(max_length=32)
    title       = models.CharField(max_length=300, blank=True)
    text        = models.TextField()
    url         = models.URLField(blank=True)
    author_id   = models.CharField(max_length=128, blank=True)
    context     = models.CharField(max_length=256, blank=True)
    language    = models.CharField(max_length=8, default="fr")
    status      = models.CharField(max_length=16, choices=STATUS_CHOICES, default="new")
    score       = models.FloatField(null=True, blank=True)
    processed   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.source}] {self.text[:60]}"

    @property
    def status_badge(self):
        return {
            "new": "badge-primary", "analysed": "badge-warning",
            "recommended": "badge-success", "drafted": "badge-warning",
            "published": "badge-success", "skipped": "badge-warning",
            "rejected": "badge-danger",
        }.get(self.status, "badge-primary")


class Recommendation(models.Model):
    opportunity  = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="recommendations")
    service      = models.ForeignKey(Service, on_delete=models.PROTECT)
    score        = models.FloatField()
    confidence   = models.FloatField()
    language     = models.CharField(max_length=8, default="fr")
    intent       = models.CharField(max_length=64, blank=True)
    reply_text   = models.TextField()
    status       = models.CharField(max_length=16, default="pending")
    reason       = models.CharField(max_length=128, blank=True)
    external_url = models.URLField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ChannelPolicy(models.Model):
    MODE_CHOICES = [("auto", "Auto"), ("draft", "Brouillon"), ("disabled", "Désactivé")]
    channel       = models.CharField(max_length=32, unique=True)
    is_enabled    = models.BooleanField(default=False)
    mode          = models.CharField(max_length=16, choices=MODE_CHOICES, default="draft")
    min_score     = models.FloatField(default=0.75)
    daily_limit   = models.IntegerField(default=10)
    require_human = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.channel} ({self.mode})"


class OptOut(models.Model):
    channel    = models.CharField(max_length=32)
    author_id  = models.CharField(max_length=128)
    context    = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("channel", "author_id", "context")


class PublicationLog(models.Model):
    channel    = models.CharField(max_length=32)
    status     = models.CharField(max_length=16)
    reason     = models.CharField(max_length=128, blank=True)
    score      = models.FloatField(null=True)
    author_id  = models.CharField(max_length=128, blank=True)
    context    = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class SearchQuery(models.Model):
    KIND_CHOICES = [
        ("brave", "Brave Search"),
        ("google_alerts", "Google Alerts RSS"),
        ("rss", "RSS générique"),
    ]
    kind       = models.CharField(max_length=16, choices=KIND_CHOICES)
    query      = models.CharField(max_length=500, blank=True)
    url        = models.URLField(blank=True)
    channel    = models.CharField(max_length=32, default="rss")
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kind}: {self.query or self.url}"


class TestScenario(models.Model):
    name             = models.CharField(max_length=200)
    text             = models.TextField()
    expected_service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL)
    last_score       = models.FloatField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
