from django.contrib import admin
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, include
from django.conf.urls import url
from django.http import JsonResponse

from rest_framework import status

schema_view = get_schema_view(
    openapi.Info(
        title="Game API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


# def custom404(request, exception=None):
#     return JsonResponse({
#         'error': 'The resource was not found'
#     }, status=status.HTTP_404_NOT_FOUND)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('game.urls')),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # url(r'^.*/$', custom404, name='error404'),
    path('jet_api/', include('jet_django.urls')),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
