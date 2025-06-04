from django.db.models import Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.products.models import Product, Category
from apps.products.serializers import ProductSerializer, ProductCreateSerializer, CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent=None).order_by('-id')
    serializer_class = CategorySerializer
    permission_classes = []

    @action(detail=False, methods=['get'])
    def all_categories(self, request):
        """Get all categories including nested ones"""
        categories = Category.objects.all().order_by('-id')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='average-price')
    def average_price(self, request, pk=None):
        """Get average product price for a category and its subcategories"""
        self.queryset = Category.objects.all()
        try:
            category = self.get_object()
            descendant_categories = category.get_descendants()
            all_categories = [category] + descendant_categories

            avg_price = Product.objects.filter(
                category__in=all_categories,
                is_active=True
            ).aggregate(avg_price=Avg('price'))['avg_price']

            return Response({
                'category': category.name,
                'category_path': ' > '.join([a.name for a in category.get_ancestors()] + [category.name]),
                'average_price': round(avg_price, 2) if avg_price else 0,
                'product_count': Product.objects.filter(
                    category__in=all_categories,
                    is_active=True
                ).count()
            }, status=status.HTTP_200_OK)

        except Category.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    permission_classes = []

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_id = self.request.query_params.get('category', None)

        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                descendant_categories = category.get_descendants()
                all_categories = [category] + descendant_categories
                queryset = queryset.filter(category__in=all_categories)
            except Category.DoesNotExist:
                pass

        return queryset

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Bulk upload products"""
        products_data = request.data if isinstance(request.data, list) else [request.data]
        created_products = []
        errors = []

        for product_data in products_data:
            serializer = ProductCreateSerializer(data=product_data)
            if serializer.is_valid():
                product = serializer.save()
                created_products.append(ProductSerializer(product).data)
            else:
                errors.append({
                    'product_data': product_data,
                    'errors': serializer.errors
                })

        return Response({
            'created': created_products,
            'errors': errors,
            'total_created': len(created_products),
            'total_errors': len(errors)
        })

