from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import success

from .permissions import IsModelOwnerOrSuperAdmin
from .serializers import MLModelCreateSerializer, MLModelSerializer
from .services import (
    ModelCapacityError,
    ModelLifecycleError,
    ModelStorageError,
    create_csv_model,
    delete_model_with_files,
    get_visible_model,
    visible_models,
)


class ModelListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        models = list(visible_models(request.user).order_by("-created_at"))
        return success(
            {
                "models": MLModelSerializer(models, many=True).data,
                "count": len(models),
            }
        )

    def post(self, request):
        serializer = MLModelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            model = create_csv_model(owner=request.user, **serializer.validated_data)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except (ModelCapacityError, ValueError) as exc:
            raise ValidationError({"model": str(exc)}) from exc
        return success(
            {"model": MLModelSerializer(model).data},
            status_code=status.HTTP_201_CREATED,
        )


class ModelDetailView(APIView):
    permission_classes = [IsAuthenticated, IsModelOwnerOrSuperAdmin]

    def get(self, request, model_id: int):
        model = _get_model(request, model_id)
        return success({"model": MLModelSerializer(model).data})

    def delete(self, request, model_id: int):
        model = _get_model(request, model_id)
        try:
            delete_model_with_files(model)
        except (ModelLifecycleError, ModelStorageError) as exc:
            raise ValidationError({"model": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


def _get_model(request, model_id: int):
    try:
        return get_visible_model(user=request.user, model_id=model_id)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
