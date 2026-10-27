# PricingApp/management/commands/collect_all.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from PricingApp.alerts_service import evaluate_and_notify

from CatalogApp.models import Product
from PricingApp.services import collect_prices_for


class Command(BaseCommand):
    help = "Collecte les prix (parallèle), évalue, envoie les alertes."

    def add_arguments(self, parser):
        parser.add_argument("--product-id", type=int, default=None)

    def handle(self, *args, **options):
        qs = Product.objects.all()
        if options["product_id"]:
            qs = qs.filter(id=options["product_id"])

        total_created = 0
        total_failed = 0

        for product in qs.iterator():
            try:
                result = collect_prices_for(product)
                alerts = evaluate_and_notify(product)

                total_created += result.created
                total_failed += result.failed

                self.stdout.write(
                    f"[{timezone.now():%H:%M:%S}] {product.title[:40]:<40} "
                    f"→ {result.created} prix, {alerts} alertes"
                    + (f", {result.failed} échecs" if result.failed else "")
                )
                for err in result.errors:
                    self.stderr.write(f"    ⚠ {err}")
            except Exception as exc:
                total_failed += 1
                self.stderr.write(f"✗ {product.title}: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"\nTerminé : {total_created} prix créés, {total_failed} échecs."
        ))