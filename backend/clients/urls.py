from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ClientGroupViewSet, TagViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename="clients")  # ✅ ОБЯЗАТЕЛЬНО `basename`
router.register(r'client-groups', ClientGroupViewSet)
router.register(r'tags', TagViewSet)


urlpatterns = [
    path('', include(router.urls)),  # <-- без 'api/'
]