"""Tests comportementaux pour le wizard batch."""
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from PricingApp.models import BatchJob

pytestmark = pytest.mark.django_db


class TestBatchNew:
    def test_requires_login(self, client):
        response = client.get(reverse("PricingApp:batch_new"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_get_renders_upload_form(self, client, user):
        client.force_login(user)
        response = client.get(reverse("PricingApp:batch_new"))
        assert response.status_code == 200

    def test_post_without_file_shows_error(self, client, user):
        client.force_login(user)
        response = client.post(reverse("PricingApp:batch_new"), {}, follow=True)
        messages = [str(m) for m in response.context["messages"]]
        assert any("Aucun fichier" in m for m in messages)

    def test_post_with_unsupported_extension_shows_error(self, client, user):
        client.force_login(user)
        upload = SimpleUploadedFile("test.exe", b"x", content_type="application/octet-stream")
        response = client.post(
            reverse("PricingApp:batch_new"), {"file": upload}, follow=True,
        )
        messages = [str(m) for m in response.context["messages"]]
        assert any("Format non supporté" in m for m in messages)
        assert not BatchJob.objects.exists()

    def test_post_with_valid_csv_creates_job_and_lines(self, client, user):
        client.force_login(user)
        content = b"Designation,Quantite,Reference\nClavier,5,\nSouris,3,\n"
        upload = SimpleUploadedFile("cmd.csv", content, content_type="text/csv")
        response = client.post(
            reverse("PricingApp:batch_new"), {"file": upload},
        )
        assert response.status_code == 302
        job = BatchJob.objects.get(user=user)
        assert job.original_name == "cmd.csv"
        assert job.original_format == "csv"
        assert job.lines.count() == 2
        assert job.column_mapping["designation"] == "Designation"
        assert job.column_mapping["quantity"] == "Quantite"


class TestBatchVerify:
    @pytest.fixture
    def job(self, user):
        return BatchJob.objects.create(
            user=user,
            original_file="batch/x.csv",
            original_name="x.csv",
            original_format="csv",
            detected_columns=["Designation", "Quantite"],
            status="verifying",
        )

    def test_get_renders_mapping_form(self, client, user, job):
        client.force_login(user)
        response = client.get(reverse("PricingApp:batch_verify", args=[job.pk]))
        assert response.status_code == 200
        assert response.context["job"].pk == job.pk

    def test_other_user_cannot_access(self, client, job):
        other = User.objects.create_user("other", password="x")
        client.force_login(other)
        response = client.get(reverse("PricingApp:batch_verify", args=[job.pk]))
        assert response.status_code == 404

    def test_post_without_designation_shows_error(self, client, user, job):
        client.force_login(user)
        response = client.post(
            reverse("PricingApp:batch_verify", args=[job.pk]),
            {"col_designation": "", "col_quantity": "Quantite"},
            follow=True,
        )
        messages = [str(m) for m in response.context["messages"]]
        assert any("Désignation" in m for m in messages)
        job.refresh_from_db()
        assert job.status == "verifying"

    def test_post_with_designation_moves_to_ready(self, client, user, job):
        client.force_login(user)
        response = client.post(
            reverse("PricingApp:batch_verify", args=[job.pk]),
            {"col_designation": "Designation", "col_quantity": "Quantite"},
        )
        assert response.status_code == 302
        job.refresh_from_db()
        assert job.status == "ready"
