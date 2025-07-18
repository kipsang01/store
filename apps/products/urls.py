from rest_framework.routers import DefaultRouter

from apps.products.views import ProductViewSet, CategoryViewSet

router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = router.urls