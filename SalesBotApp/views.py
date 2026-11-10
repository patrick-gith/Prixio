import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .engine import match_services, recommend
from .forms import (
    ChannelPolicyForm,
    CSVImportForm,
    PlaygroundForm,
    SearchQueryForm,
    ServiceForm,
)
from .models import (
    ChannelPolicy,
    Opportunity,
    PublicationLog,
    Recommendation,
    SearchQuery,
    Service,
)


@login_required
def dashboard(request):
    week_ago = timezone.now() - timezone.timedelta(days=7)
    stats = {
        "services_active": Service.objects.filter(is_active=True).count(),
        "services_total": Service.objects.count(),
        "opps_total": Opportunity.objects.count(),
        "opps_week": Opportunity.objects.filter(created_at__gte=week_ago).count(),
        "recs_total": Recommendation.objects.count(),
        "recs_pending": Recommendation.objects.filter(status="pending").count(),
        "recs_published": Recommendation.objects.filter(status="published").count(),
        "recs_week": Recommendation.objects.filter(created_at__gte=week_ago).count(),
    }
    by_channel = Opportunity.objects.values("channel").annotate(total=Count("id")).order_by("-total")
    recent_recs = Recommendation.objects.select_related("service", "opportunity").order_by("-created_at")[:8]
    recent_logs = PublicationLog.objects.order_by("-created_at")[:10]
    return render(request, "SalesBotApp/dashboard.html", {
        "stats": stats, "by_channel": by_channel,
        "recent_recs": recent_recs, "recent_logs": recent_logs,
    })


@login_required
def services_list(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "").strip()
    qs = Service.objects.all().order_by("category", "title")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q)
                       | Q(keywords_fr__icontains=q) | Q(keywords_en__icontains=q))
    if cat:
        qs = qs.filter(category=cat)
    return render(request, "SalesBotApp/services_list.html", {
        "services": qs, "q": q, "cat": cat, "categories": Service.CATEGORY_CHOICES,
    })


@login_required
def service_edit(request, pk=None):
    obj = get_object_or_404(Service, pk=pk) if pk else None
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Prestation enregistrée.")
            return redirect("SalesBotApp:services_list")
    else:
        form = ServiceForm(instance=obj)
    return render(request, "SalesBotApp/service_form.html", {"form": form, "obj": obj})


@login_required
def import_csv(request):
    if request.method == "POST":
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data["file"].read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(data))
            created = updated = 0
            for row in reader:
                slug = (row.get("slug") or row.get("title", "").lower().replace(" ", "-")).strip()
                if not slug:
                    continue
                _, c = Service.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "title": row.get("title", "").strip(),
                        "url_comeup": (row.get("url_comeup") or row.get("url") or "").strip(),
                        "description": row.get("description", "").strip(),
                        "keywords_fr": row.get("keywords_fr", "").strip(),
                        "keywords_en": row.get("keywords_en", "").strip(),
                        "category": (row.get("category") or "automation").strip(),
                        "is_active": form.cleaned_data["activate"],
                    },
                )
                created += int(c)
                updated += int(not c)
            messages.success(request, f"Import terminé : {created} créés, {updated} mis à jour.")
            return redirect("SalesBotApp:services_list")
    else:
        form = CSVImportForm()
    return render(request, "SalesBotApp/import_csv.html", {"form": form})


@login_required
def opportunities_list(request):
    q = request.GET.get("q", "").strip()
    channel = request.GET.get("channel", "").strip()
    status = request.GET.get("status", "").strip()
    qs = Opportunity.objects.all()
    if q:
        qs = qs.filter(Q(text__icontains=q) | Q(title__icontains=q))
    if channel:
        qs = qs.filter(channel=channel)
    if status:
        qs = qs.filter(status=status)
    return render(request, "SalesBotApp/opportunities_list.html", {
        "opps": qs[:200], "q": q, "channel": channel, "status": status,
    })


@login_required
def opportunity_detail(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "analyse":
            rec = recommend(opp.text)
            if rec:
                Recommendation.objects.create(
                    opportunity=opp, service=rec.service,
                    score=rec.score, confidence=rec.confidence,
                    language=rec.language, intent=rec.intent,
                    reply_text=rec.reply,
                )
                opp.status = "recommended"
                opp.score = rec.score
                opp.save(update_fields=["status", "score"])
                messages.success(request, "Recommandation générée.")
            else:
                messages.warning(request, "Aucun match pertinent.")
        elif action == "publish":
            r = Recommendation.objects.filter(opportunity=opp, status="pending").first()
            if r:
                r.status = "published"
                r.save(update_fields=["status"])
                PublicationLog.objects.create(channel=opp.channel, status="published",
                                              score=r.score, context=opp.context)
                opp.status = "published"
                opp.save(update_fields=["status"])
                messages.success(request, "Publication enregistrée.")
        elif action == "reject":
            opp.status = "rejected"
            opp.save(update_fields=["status"])
            messages.info(request, "Opportunité rejetée.")
        return redirect("SalesBotApp:opportunity_detail", pk=pk)
    return render(request, "SalesBotApp/opportunity_detail.html", {"opp": opp})


@login_required
def opportunities_bulk(request):
    if request.method != "POST":
        return redirect("SalesBotApp:opportunities_list")
    ids = request.POST.getlist("ids")
    action = request.POST.get("action")
    qs = Opportunity.objects.filter(id__in=ids)
    count = qs.count()
    if action == "analyse":
        for opp in qs:
            rec = recommend(opp.text)
            if rec:
                Recommendation.objects.create(
                    opportunity=opp, service=rec.service,
                    score=rec.score, confidence=rec.confidence,
                    language=rec.language, intent=rec.intent,
                    reply_text=rec.reply,
                )
                opp.status = "recommended"
                opp.score = rec.score
                opp.save(update_fields=["status", "score"])
    elif action == "reject":
        qs.update(status="rejected")
    messages.success(request, f"{count} opportunité(s) traitée(s).")
    return redirect("SalesBotApp:opportunities_list")


@login_required
def playground(request):
    result = None
    matches = None
    form = PlaygroundForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        text = form.cleaned_data["text"]
        rec = recommend(text)
        if rec:
            matches = match_services(text, top_k=3)
            result = rec
        else:
            messages.warning(request, "Aucun match pertinent. Ajustez les seuils ou les mots-clés.")
    return render(request, "SalesBotApp/playground.html", {
        "form": form, "result": result, "matches": matches,
    })


def _seed_policies():
    defaults = [
        ("telegram", "auto", True, 0.68, 100),
        ("discord", "draft", False, 0.82, 5),
        ("quora", "draft", False, 0.75, 10),
        ("reddit", "draft", False, 0.75, 10),
        ("google", "draft", False, 0.75, 10),
        ("rss", "draft", False, 0.72, 20),
    ]
    for ch, mode, enabled, score, limit in defaults:
        ChannelPolicy.objects.get_or_create(
            channel=ch,
            defaults={"mode": mode, "is_enabled": enabled,
                      "min_score": score, "daily_limit": limit,
                      "require_human": mode != "auto"},
        )


@login_required
def channels(request):
    _seed_policies()
    policies = ChannelPolicy.objects.all().order_by("channel")
    return render(request, "SalesBotApp/channels.html", {"policies": policies})


@login_required
def channel_edit(request, pk):
    policy = get_object_or_404(ChannelPolicy, pk=pk)
    if request.method == "POST":
        form = ChannelPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, f"Canal {policy.channel} mis à jour.")
            return redirect("SalesBotApp:channels")
    else:
        form = ChannelPolicyForm(instance=policy)
    return render(request, "SalesBotApp/channel_form.html", {"form": form, "policy": policy})


@login_required
def search_queries(request):
    qs = SearchQuery.objects.all().order_by("-created_at")
    if request.method == "POST":
        form = SearchQueryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Requête ajoutée.")
            return redirect("SalesBotApp:search_queries")
    else:
        form = SearchQueryForm()
    return render(request, "SalesBotApp/search_queries.html", {"queries": qs, "form": form})


@login_required
def logs(request):
    return render(request, "SalesBotApp/logs.html", {
        "logs": PublicationLog.objects.order_by("-created_at")[:500],
    })
