from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import MLModel, ModelStatus, ModelType


User = get_user_model()


class ModelApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.developer = self.create_user("developer@example.com", "DEVELOPER")
        self.other_developer = self.create_user("other@example.com", "DEVELOPER")
        self.admin = self.create_user("admin@example.com", "SUPER_ADMIN")

    def create_user(self, email, role):
        extra_fields = {
            "role": role,
            "approval_status": "APPROVED",
            "is_active": True,
            "email_verified": True,
        }
        if role == "SUPER_ADMIN":
            return User.objects.create_superuser(
                name="Admin",
                email=email,
                password="correct horse battery staple",
            )
        return User.objects.create_user(
            name="Developer",
            email=email,
            password="correct horse battery staple",
            **extra_fields,
        )

    def authenticate(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_developer_can_create_csv_model(self):
        self.authenticate(self.developer)

        response = self.client.post(
            reverse("model-list-create"),
            {
                "name": "Developer model",
                "description": "A test model",
                "model_type": ModelType.CSV,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["model"]["model_type"], ModelType.CSV)
        self.assertEqual(response.data["data"]["model"]["status"], ModelStatus.DRAFT)
        self.assertEqual(response.data["data"]["model"]["owner"], self.developer.id)

    def test_image_model_type_is_not_available(self):
        self.authenticate(self.developer)

        response = self.client.post(
            reverse("model-list-create"),
            {"name": "Image model", "model_type": ModelType.IMAGE},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

    def test_developer_only_sees_owned_models(self):
        owned_model = MLModel.objects.create(
            owner=self.developer,
            name="Owned model",
            model_type=ModelType.CSV,
        )
        MLModel.objects.create(
            owner=self.other_developer,
            name="Other model",
            model_type=ModelType.CSV,
        )
        self.authenticate(self.developer)

        response = self.client.get(reverse("model-list-create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(response.data["data"]["models"][0]["id"], owned_model.id)

    def test_developer_cannot_read_another_developers_model(self):
        model = MLModel.objects.create(
            owner=self.other_developer,
            name="Private model",
            model_type=ModelType.CSV,
        )
        self.authenticate(self.developer)

        response = self.client.get(reverse("model-detail", args=[model.id]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["success"])

    def test_super_admin_can_see_all_models(self):
        MLModel.objects.create(
            owner=self.developer,
            name="Developer model",
            model_type=ModelType.CSV,
        )
        MLModel.objects.create(
            owner=self.other_developer,
            name="Other model",
            model_type=ModelType.CSV,
        )
        self.authenticate(self.admin)

        response = self.client.get(reverse("model-list-create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 2)

    def test_developer_can_delete_draft_model(self):
        model = MLModel.objects.create(
            owner=self.developer,
            name="Draft model",
            model_type=ModelType.CSV,
        )
        self.authenticate(self.developer)

        response = self.client.delete(reverse("model-detail", args=[model.id]))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(MLModel.objects.filter(pk=model.pk).exists())

    def test_model_api_does_not_expose_artifact_path(self):
        model = MLModel.objects.create(
            owner=self.developer,
            name="Trained model",
            model_type=ModelType.CSV,
            status=ModelStatus.TRAINED,
            artifact_reference="trained_models/1/model.joblib",
            metadata={"artifact_reference": "trained_models/1/model.joblib"},
        )
        self.authenticate(self.developer)

        response = self.client.get(reverse("model-detail", args=[model.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("artifact_reference", response.data["data"]["model"])
        self.assertNotIn(
            "artifact_reference",
            response.data["data"]["model"]["metadata"],
        )
        self.assertTrue(response.data["data"]["model"]["has_artifact"])

    def test_trained_model_can_be_deleted_with_artifact_cleanup(self):
        model = MLModel.objects.create(
            owner=self.developer,
            name="Trained model",
            model_type=ModelType.CSV,
            status=ModelStatus.TRAINED,
        )
        self.authenticate(self.developer)

        response = self.client.delete(reverse("model-detail", args=[model.id]))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(MLModel.objects.filter(pk=model.pk).exists())

