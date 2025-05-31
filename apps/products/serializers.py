from rest_framework import serializers

from apps.products.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'children', 'path']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []

    def get_path(self, obj):
        """Return full category path like 'All Products > Bakery > Bread'"""
        path = [ancestor.name for ancestor in obj.get_ancestors()]
        path.append(obj.name)
        return ' > '.join(path)


class ProductSerializer(serializers.ModelSerializer):
    category_path = serializers.CharField(source='category.get_path', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category',
            'category_name', 'category_path', 'sku',
            'stock_quantity', 'is_active'
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    """Separate serializer for product creation to handle category paths"""
    category_path = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category',
            'category_path', 'sku', 'stock_quantity', 'is_active'
        ]

    def create(self, validated_data):
        category_path = validated_data.pop('category_path', None)

        if category_path and 'category' not in validated_data:
            # Find or create category hierarchy
            category = self._get_or_create_category_from_path(category_path)
            validated_data['category'] = category

        return super().create(validated_data)

    def _get_or_create_category_from_path(self, path):
        """Create category hierarchy from path like 'Bakery > Bread > Sourdough'"""
        categories = [name.strip() for name in path.split('>')]
        parent = None

        for category_name in categories:
            category, _ = Category.objects.get_or_create(
                name=category_name,
                parent=parent
            )
            parent = category

        return parent
