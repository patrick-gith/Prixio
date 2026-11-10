from django.contrib import admin

from .models import (
    ChannelPolicy,
    Opportunity,
    OptOut,
    PublicationLog,
    Recommendation,
    SearchQuery,
    Service,
    TestScenario,
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "price")
    list_filter = ("category", "is_active")
    search_fields = ("title", "description", "keywords_fr", "keywords_en")


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("source", "channel", "status", "score", "created_at")
    list_filter = ("source", "channel", "status")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("id", "opportunity", "service", "score", "status", "created_at")
    list_filter = ("status", "language")


@admin.register(ChannelPolicy)
class ChannelPolicyAdmin(admin.ModelAdmin):
    list_display = ("channel", "mode", "is_enabled", "min_score", "daily_limit")


@admin.register(OptOut)
class OptOutAdmin(admin.ModelAdmin):
    list_display = ("channel", "author_id", "context", "created_at")


@admin.register(PublicationLog)
class PublicationLogAdmin(admin.ModelAdmin):
    list_display = ("channel", "status", "reason", "score", "created_at")
    list_filter = ("channel", "status")


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("kind", "query", "url", "channel", "is_active")


@admin.register(TestScenario)
class TestScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "expected_service", "last_score", "created_at")
