from django.urls import path

from .views import ModelDetailView, ModelListCreateView


urlpatterns = [
    path("", ModelListCreateView.as_view(), name="model-list-create"),
    path("<int:model_id>/", ModelDetailView.as_view(), name="model-detail"),
]
