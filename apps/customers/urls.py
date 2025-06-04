from django.urls import path

from apps.customers.views import CustomerViewSet

app_name = 'customers'

urlpatterns = [
    path('', CustomerViewSet.as_view({'get': 'list'}), name='customer'),
    ]
