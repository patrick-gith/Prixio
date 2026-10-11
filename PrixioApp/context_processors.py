from django.conf import settings


def prixio_context(request):
    return {
        "COMPANY_NAME": settings.COMPANY_NAME,
        "COMPANY_EMAIL": settings.COMPANY_EMAIL,
        "BASE_CURRENCY": settings.BASE_CURRENCY,
    }
