from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Vista de esquema Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="API de Gestión de Usuarios",
      default_version='v1',
      description="API para gestión de usuarios y autenticación",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # URLs de administración
    path('admin/', admin.site.urls),
    
    # URLs de Swagger
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # URLs de JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # URLs de usuarios
    path('api/', include('users.urls')),
    
    # URLs de autenticación personalizada
    path('api/auth/', include('authentication.urls')),
]