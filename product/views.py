from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.http import Http404
from django.contrib.auth.models import Group
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from rest_framework import status
from .models import Category
from users.permissions import IsAdminGroupUser

class SingleProductView(APIView):
    serializer_class = ProductSerializer
    def get(self,request,id):
        try:
            product = Product.objects.get(id=id)
            obj = ProductSerializer(product, context={"request": request})
            return Response(obj.data)
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=404)


class RateView(APIView):
    serializer_class = RateSerializer
    # ?
    def get(self, request):
        objects = Rate.objects.all()
        serializer = self.serializer_class(objects, many=True)
        return Response({"context": serializer.data})


class SingleRateView(APIView):
    serializer_class = RateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request,id):

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404("Product not found")
        rate_value = request.data.get("rate")
        if not rate_value:
            return Response("You must provide a rating.", status=400)
        rated = Rate.objects.filter(product=product, rated_by=request.user).first()
        if rated:
            return Response("You have already rated this product.", status=400)
        else:
            new_rate = Rate.objects.create(
                product=product, rated_by=request.user, rate=rate_value
            )
            all_ratings = Rate.objects.filter(product=product)
            total_ratings = sum([r.rate for r in all_ratings])
            average_rate = total_ratings / len(all_ratings)
            product.average_rate = average_rate
            product.save()
            return Response("You have rated the product.", status=201)
        
    def put(self, request, id):
        
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404("Product not found")
        rate_value = request.data.get("rate")
        if not rate_value:
            return Response("You must provide a rating.", status=400)
        rated = Rate.objects.filter(product=product, rated_by=request.user).first()
        if not rated:
            return Response("You have not rated this product before.", status=400)
        rated.rate = rate_value
        rated.save()
        all_ratings = Rate.objects.filter(product=product)
        total_ratings = sum([r.rate for r in all_ratings])
        average_rate = total_ratings / len(all_ratings)
        product.average_rate = average_rate
        product.save()
        return Response("You have updated your rating for the product.", status=200)
    
    def delete(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404("Product not found")
        rated = Rate.objects.filter(product=product, rated_by=request.user).first()
        if not rated:
            return Response("You have not rated this product before.", status=400)
        rated.delete()
        all_ratings = Rate.objects.filter(product=product)
        if all_ratings.exists():
            total_ratings = sum([r.rate for r in all_ratings])
            average_rate = total_ratings / len(all_ratings)
        else:
            average_rate = 0  
        product.average_rate = average_rate
        product.save()
        return Response("Your rating has been deleted.", status=200)


class PopularProductView(APIView):
    serializer_class = ProductSerializer

    def get(self, request):
        best_product = Product.objects.all().order_by(
            "-average_rate"
        )[:10]
        serializer = self.serializer_class(
            best_product, many=True, context={"request": request}
        ).data

        return Response(serializer)

class DiscountView(APIView):
    serializer_class = ProductSerializer

    def get(self, request):
        best_product = Product.objects.all().order_by("-discount")
        serializer = self.serializer_class(
            best_product, many=True, context={"request": request}
        ).data

        return Response(serializer)

class AllProductView(APIView):
    serializer_class = ProductSerializer

    def get(self, request):
        all_product = Product.objects.all()
        serializer = self.serializer_class(
            all_product, many=True, context={"request": request}
        ).data

        return Response(serializer)

class ProductCommentView(APIView):
    serializer_class = ProductCommentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request,id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404("Product not found")
        
        serializer = self.serializer_class(
            data=request.data,
            context={'user': request.user, 'product': product}
        )
        if serializer.is_valid():
            serializer.save()
            return Response("You have commented the product.", status=201)
        return Response(
            {"message": "Something went wrong", "errors": serializer.errors}, status=400
        )
class SingleProductCommentsView(APIView):
    serializer_class = ProductCommentSerializer
    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404("Product not found")
        comments = product.comments.select_related('user').all()
        ratings = product.ratings.select_related('rated_by').all()

        rating_map = {
            (rating.rated_by): rating.rate
            for rating in ratings
        }

        response_data = [
        {
            "user_name": comment.user.username,
            "comment": comment.comment,
            "suggested":comment.suggested,
            "posted_at": comment.posted_at,
            "rating": rating_map.get(comment.user_id),
        } for comment in comments
        ]
        return Response(response_data)

class CategoryView(APIView):
    serializer_class = ProductSerializer

    category_map = {
        1: "نان بربری",
        2: "نان سنگک",
        3: "نان تافتون",
        4: "نان محلی",
        5: "نان فانتزی",
        6: "نان لواش",
    }

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category",
                description="Enter Category number",
                required=True,
                type=int,
            ),
        ]
    )
    def get(self, request):
        category_param = request.query_params.get("category")

        if not category_param:
            return Response({"error": "Enter a Category"}, status=400)

        try:
            category = int(category_param)
        except ValueError:
            return Response({"error": "Category must be an integer"}, status=400)

        category_name = self.category_map.get(category)
        if not category_name:
            return Response({"error": "Invalid category number"}, status=400)

        items = Product.objects.filter(category__category=category_name)
        serializer = self.serializer_class(
            items, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CategoryBoxView(APIView):
    serializer_class = ProductSerializer

    category_map = {
        1: "نان بربری",
        2: "نان سنگک",
        3: "نان تافتون",
        4: "نان محلی",
        5: "نان فانتزی",
        6: "نان لواش",
    }

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category",
                description="Enter category number (1-6)",
                required=True,
                type=int,
            ),
            OpenApiParameter(
                name="box_type",
                description="Enter box type number (1, 2, 4, 6, or 8)",
                required=True,
                type=int,
            ),
        ]
    )
    def get(self, request):
        category_param = request.query_params.get("category")
        box_param = request.query_params.get("box_type")

        if not category_param or not box_param:
            return Response(
                {"error": "Both 'category' and 'box_type' parameters are required."},
                status=400,
            )

        try:
            category = int(category_param)
            box = int(box_param)
        except ValueError:
            return Response(
                {"error": "Both 'category' and 'box_type' must be integers."},
                status=400,
            )

        category_name = self.category_map.get(category)
        if not category_name:
            return Response({"error": "Invalid category number."}, status=400)

        if box not in [1, 2, 4, 6, 8]:
            return Response(
                {"error": "Invalid box_type. Must be one of 1, 2, 4, 6, 8."}, status=400
            )

        products = Product.objects.filter(
            category__category=category_name, box_type=box
        )
        serializer = self.serializer_class(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)

class AdminProductDisply(APIView):
    serializer_class = AdminProductSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    def get(self, request):
        products = Product.objects.all()
        serializer = self.serializer_class(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminFilterProduct(ListAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AdminProductView(APIView):
    serializer_class = AdminProductSerializer
    # parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Product saved successfully"}, status=status.HTTP_201_CREATED
            )

        return Response(
            {"message": "Something went wrong", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminSingleProductView(APIView):
    serializer_class = AdminProductSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def put(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404("Product not found")

        serializer = self.serializer_class(
            product, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Product updated successfully"})

        return Response(
            {"message": "Something went wrong", "errors": serializer.errors}, status=400
        )

    def delete(self, request, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()
            return Response({"message": "Product deleted successfully"})
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=404)


class CategoryNameView(APIView):
    serializer_class = CategoryNameSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    def get(self, request):

        categories = Category.objects.all().order_by("id")
        serializer = self.serializer_class(
            categories, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CategoryCreationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = CategoryCreationSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            data = serializer.validated_data
            serializer.save(photo=data.get("photo"))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryModifyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = CategoryCreationSerializer

    def get_object(self, id):
        try:
            return Category.objects.get(id=id)
        except Category.DoesNotExist:
            return None

    def put(self, request, id):
        category = self.get_object(id)
        if not category:
            return Response(
                {"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(
            category, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            data = serializer.validated_data
            serializer.save(photo=data.get("photo"))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        category = self.get_object(id)
        if not category:
            return Response(
                {"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        category.delete()
        return Response(
            {"message": "Category deleted"}, status=status.HTTP_204_NO_CONTENT
        )
