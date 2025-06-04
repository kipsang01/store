from django.contrib import admin
from django.urls import path, include

from store.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/customer/', include('apps.customers.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/', include('apps.products.urls')),
    path('health-check/', health_check),
]
