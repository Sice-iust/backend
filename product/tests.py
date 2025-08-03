from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from .models import Product, Subcategory, Rate, ProductComment,Category
from .serializers import ProductCommentSerializer
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import tempfile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from product.serializers import *

User = get_user_model()
from django.test import TestCase,RequestFactory
from rest_framework.test import APIRequestFactory,force_authenticate
from .models import *
from .serializers import *
from .views import *

class SingleProductCommentsViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = SingleProductCommentsView.as_view()
        self.user = User.objects.create_user(username="fati", password="pass123")
        self.other_user = User.objects.create_user(username="guest", password="pass456")

        self.category = Category.objects.create(category="Gadgets", box_color="Cyan")
        self.product = Product.objects.create(
            name="Bluetooth Speaker", price=49.99, category=self.category
        )

        ProductComment.objects.create(
            comment="Great sound quality",
            product=self.product,
            user=self.user,
            suggested=ProductComment.SUGGESTED,
        )

        Rate.objects.create(product=self.product, rated_by=self.user, rate=4.5)
        Rate.objects.create(product=self.product, rated_by=self.other_user, rate=3.0)

    def test_get_product_comments_and_ratings(self):
        request = self.factory.get("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request, id=self.product.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        comment_data = response.data[0]
        self.assertEqual(comment_data["user_name"], "fati")
        self.assertEqual(comment_data["comment"], "Great sound quality")
        self.assertEqual(comment_data["suggested"], ProductComment.SUGGESTED)
        self.assertEqual(comment_data["rating"], 4.5)

    def test_product_not_found(self):
        request = self.factory.get("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request, id=9999) 

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PopularProductViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = PopularProductView.as_view()

        self.category = Category.objects.create(category="Tech", box_color="Blue")

        for i in range(12):
            Product.objects.create(
                name=f"Product {i}",
                price=10 + i,
                category=self.category,
                average_rate=float(i),
            )

    def test_get_popular_products(self):
        request = self.factory.get("/popular-products/")
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

        rates = [product["average_rate"] for product in response.data]
        self.assertEqual(rates, sorted(rates, reverse=True))
        self.assertEqual(response.data[0]["name"], "Product 11")


class ProductSerializerTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.request = self.factory.get("/")
        self.category = Category.objects.create(category="Books", box_color="Red")
        self.product = Product.objects.create(
            name="Advanced Python",
            price=120.00,
            discount=25,
            category=self.category,
            stock=100,
            box_type=2,
            average_rate=4.666,
        )

    def test_discounted_price_calculation(self):
        serializer = ProductSerializer(
            instance=self.product, context={"request": self.request}
        )
        self.assertIn("discounted_price", serializer.data)
        self.assertEqual(serializer.data["discounted_price"], 90.0)

    def test_average_rate_rounding(self):
        serializer = ProductSerializer(
            instance=self.product, context={"request": self.request}
        )
        self.assertEqual(serializer.data["average_rate"], 4.7)

    def test_category_fields(self):
        serializer = ProductSerializer(
            instance=self.product, context={"request": self.request}
        )
        self.assertEqual(serializer.data["category"], "Books")
        self.assertEqual(serializer.data["box_color"], "Red")

    def test_photo_url_empty(self):
        serializer = ProductSerializer(
            instance=self.product, context={"request": self.request}
        )
        self.assertIsNone(serializer.data["photo_url"])


class RateSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category="Books", box_color="Blue")
        self.product = Product.objects.create(
            name="Clean Architecture", price=75.00, category=self.category
        )
        self.user = User.objects.create_user(username="techie", password="mouse123",phonenumber="+989036635478",email="test122@gmail.com")

        self.rate = Rate.objects.create(
            product=self.product, rated_by=self.user, rate=4.5
        )

    def test_rate_serializer_output(self):
        serializer = RateSerializer(instance=self.rate)
        data = serializer.data
        self.assertEqual(data["rate"], 4.5)
        self.assertEqual(data["product"]["id"], self.product.id)
        self.assertEqual(data["product"]["name"], "Clean Architecture")


class ProductCommentModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            category="Accessories", box_color="Green"
        )
        self.product = Product.objects.create(
            name="Wireless Mouse", price=45.99, category=self.category
        )
        self.user = User.objects.create_user(username="techie", password="mouse123",phonenumber="+989036635478",email="test122@gmail.com")

    def test_create_product_comment(self):
        comment = ProductComment.objects.create(
            comment="Really smooth and responsive!",
            product=self.product,
            user=self.user,
            suggested=ProductComment.SUGGESTED,
        )
        self.assertEqual(comment.comment, "Really smooth and responsive!")
        self.assertEqual(comment.product.name, "Wireless Mouse")
        self.assertEqual(comment.user.username, "techie")
        self.assertEqual(comment.suggested, ProductComment.SUGGESTED)


class PostProductAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            price=Decimal("100.00"),
            description="Test Description",
            stock=10,
            box_type=2,

            color="Blue",
            discount=Decimal(10),
        )
        Subcategory.objects.create(product=self.product, subcategory="Fresh")
        self.url = reverse("product-post")

    def _generate_image(self):
        image = Image.new("RGB", (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(tmp_file, format="JPEG")
        tmp_file.seek(0)
        return SimpleUploadedFile(
            "test.jpg", tmp_file.read(), content_type="image/jpeg"
        )

    def test_create_product_with_subcategories_no_admin(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="fati@gmail.com",
            phonenumber="+989034488755"
        )
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        # self.user.groups.add(admin_group)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        image = self._generate_image()
        data = {
            "category": self.category,
            "name": "New Product",
            "price": "200.00",
            "description": "Description here",
            "stock": 5,
            "box_type": 3,
            "box_color": "Green",
            "color": "Yellow",
            "discount": 15,
            "photo": image,
            "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
        }
        response = self.client.post(self.url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["message"], "Permission denied")

    def test_create_product_with_subcategories_no_box(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="fati@gmail.com",
            phonenumber="+989034488755",
        )
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user.groups.add(admin_group)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        image = self._generate_image()
        data = {
            "category":self.category,
            "name": "New Product",
            "price": Decimal(200.00),
            "description": "Description here",
            "stock": 5,
            "box_type": 3,
            "box_color": "Green",
            "color": "Yellow",
            "discount": 15,
            "photo": image,
            "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
        }

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_with_subcategories(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="fati@gmail.com",
            phonenumber="+989034488755",
        )
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user.groups.add(admin_group)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        image = self._generate_image()
        data = {
            "category":self.category,
            "name": "New Product",
            "price": Decimal(200.00),
            "description": "Description here",
            "stock": 5,
            "box_type": 4,
            "box_color": "Green",
            "color": "Yellow",
            "discount": 15,
            "photo": image,
            "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
        }

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Product saved successfully")
        product = Product.objects.get(name="New Product")
        self.assertEqual(product.name, "New Product")

        self.assertEqual(Decimal(product.price), Decimal(200.00))

    def test_create_product_missing_required_fields(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="fati@gmail.com",
            phonenumber="+989034488755",
        )
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user.groups.add(admin_group)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        data = {
            "category":"barbari",
            "name": "",
            "price": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SingleProductAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            price=Decimal("100.00"),
            description="Test Description",
            stock=10,
            box_type=2,

            color="Blue",
            discount=Decimal(10),
        )
        Subcategory.objects.create(product=self.product, subcategory="Fresh")
        self.url = reverse("product-single",args=[self.product.id])
    def _generate_image(self):
        image = Image.new("RGB", (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(tmp_file, format="JPEG")
        tmp_file.seek(0)
        return SimpleUploadedFile(
            "test.jpg", tmp_file.read(), content_type="image/jpeg"
        )
    def test_get_single_product_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Product")
        self.assertEqual(
            response.data["category"], "barbari"
        )
        self.assertEqual(Decimal(response.data["price"]), Decimal("100.00"))
        self.assertEqual(response.data["stock"], 10)
        self.assertEqual(response.data["discount"], 10)

        subcategories = [sub["subcategory"] for sub in response.data["subcategories"]]
        self.assertIn("Fresh", subcategories)

    def test_get_single_product_not_found(self):
        invalid_id = self.product.id + 55
        url = reverse("product-single", args=[invalid_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Product not found")


class AdminSingleProductAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.user = User.objects.create_user(
            username="adminuser",
            password="adminpass",
            email="admin@example.com",
            phonenumber="+989034488755",
        )
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user.groups.add(admin_group)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            price=Decimal("100.00"),
            description="Test Description",
            stock=10,
            box_type=2,

            color="Blue",
            discount=Decimal(10),
        )
        self.url = reverse("admin-product-single", args=[self.product.id])
        self.invalid_url = reverse("admin-product-single", args=[9999])

    def test_update_product_success(self):
        data = {
            "name": "Updated Product",
            "price": "120.00",
            "stock": 15,
        }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Product updated successfully")
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Updated Product")
        self.assertEqual(self.product.price, Decimal("120.00"))
        self.assertEqual(self.product.stock, 15)

    def test_update_product_not_found(self):
        data = {
            "name": "Not Found",
        }
        response = self.client.put(self.invalid_url, data)
        self.assertEqual(response.status_code, 404)

    def test_delete_product_success(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Product deleted successfully")
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_delete_product_not_found(self):
        response = self.client.delete(self.invalid_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["message"], "Product not found")

    def test_update_permission_denied(self):
        self.user.groups.clear()
        data = {"name": "Hack Attempt"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["message"], "Permission denied")

    def test_delete_permission_denied(self):
        self.user.groups.clear()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["message"], "Permission denied")


class RateViewAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.user = User.objects.create_user(
            username="adminuser",
            password="adminpass",
            email="admin@example.com",
            phonenumber="+989034488755",
        )
        self.user2 = User.objects.create_user(
            username="adminuser2",
            password="adminpass2",
            email="admin2@example.com",
            phonenumber="+989034488752",
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Sample Product",
            price=Decimal("50.00"),
            description="A great bread",
            stock=20,
            box_type=1,

            color="Brown",
            discount=Decimal(5),
        )

        self.rate1 = Rate.objects.create(product=self.product, rate=Decimal("4.5"),rated_by=self.user)
        self.rate2 = Rate.objects.create(product=self.product, rate=Decimal("3.8"),rated_by=self.user2)

        self.url = reverse("rate-view")

    def test_get_rate_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("context", response.data)
        self.assertEqual(len(response.data["context"]), 2)

        rate_data = response.data["context"][0]
        self.assertIn("product", rate_data)
        self.assertIn("rate", rate_data)
        self.assertEqual(Decimal(rate_data["rate"]), Decimal("4.5"))


class SingleRateViewAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.user = User.objects.create_user(
            username="adminuser",
            password="adminpass",
            email="admin@example.com",
            phonenumber="+989034488755",
        )

        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user.groups.add(admin_group)

        self.product = Product.objects.create(
            category=self.category2,
            name="Sample Product",
            price=Decimal("50.00"),
            description="A great bread",
            stock=20,
            box_type=1,

            color="Brown",
            discount=Decimal(5),
        )

        self.url = reverse("rate-add", kwargs={"id": self.product.id})

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_post_create_rating(self):
        response = self.client.post(self.url, {"rate": "4.5"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rate.objects.count(), 1)
        self.assertEqual(Rate.objects.first().rate, Decimal("4.5"))

    def test_post_duplicate_rating(self):
        Rate.objects.create(
            product=self.product, rate=Decimal("3.5"), rated_by=self.user
        )
        response = self.client.post(self.url, {"rate": "4.5"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_update_rating(self):
        Rate.objects.create(
            product=self.product, rate=Decimal("3.0"), rated_by=self.user
        )
        response = self.client.put(self.url, {"rate": "4.7"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(float(self.product.average_rate), 4.7)

    def test_delete_rating(self):
        Rate.objects.create(
            product=self.product, rate=Decimal("4.0"), rated_by=self.user
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rate.objects.count(), 0)

    def test_unauthorized_access(self):
        self.client.credentials()
        response = self.client.post(self.url, {"rate": "5"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ProductCommentViewsTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.user = User.objects.create_user(
            username="commenter",
            password="commentpass",
            email="commenter@example.com",
            phonenumber="+989034488755"
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.product = Product.objects.create(
            category=self.category2,
            name="Commented Bread",
            price=Decimal("70.00"),
            description="Tasty bread",
            stock=20,
            box_type=1,

            color="Tan",
            discount=Decimal("7.5"),
            average_rate=4.0,
        )

        self.comment_url = f"/user/comment/product/{self.product.id}"
        self.comments_list_url = f"/product/comments/{self.product.id}/"

    def test_create_comment_authenticated(self):
        data = {
            "comment": "Very fresh bread!",
            "suggested": 3  # suggested
        }
        response = self.client.post(self.comment_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductComment.objects.count(), 1)
        self.assertEqual(ProductComment.objects.first().comment, "Very fresh bread!")

    def test_create_comment_unauthenticated(self):
        self.client.credentials()  # Remove auth header
        data = {
            "comment": "No auth comment",
            "suggested": 2
        }
        response = self.client.post(self.comment_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_comments(self):
        ProductComment.objects.create(
            product=self.product,
            user=self.user,
            comment="This is great!",
            suggested=3
        )
        response = self.client.get(self.comments_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["comment"], "This is great!")
        self.assertEqual(response.data[0]["user_name"], self.user.username)

    def test_comment_on_nonexistent_product(self):
        invalid_id = self.product.id + 999
        data = {"comment": "Trying with invalid product", "suggested": 1}
        response = self.client.post(f"/user/comment/product/{invalid_id}", data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_comments_nonexistent_product(self):
        invalid_id = self.product.id + 999
        response = self.client.get(f"/product/comments/{invalid_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_comment_missing_fields(self):
        data = {}  # empty payload
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_create_comment_invalid_suggested_value(self):
        data = {
            "comment": "Invalid suggestion",
            "suggested": 99  # invalid choice
        }
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_serializer_without_context_fails_gracefully(self):
        data = {"comment": "Test", "suggested": 1}
        serializer = ProductCommentSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # valid fields
        with self.assertRaises(serializers.ValidationError):  # should crash when saving
            serializer.save()

    def test_comment_response_without_rating(self):
        ProductComment.objects.create(
            product=self.product,
            user=self.user,
            comment="Comment without rating",
            suggested=1
        )
        response = self.client.get(self.comments_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["rating"], None)

    def test_large_number_of_comments(self):
        for i in range(100):
            ProductComment.objects.create(
                product=self.product,
                user=self.user,
                comment=f"Comment #{i}",
                suggested=1
            )
        response = self.client.get(self.comments_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 100)

    def test_sql_injection_in_url(self):
        malicious_id = "1; DROP TABLE users"  # invalid type
        response = self.client.get(f"/product/comments/{malicious_id}/")
        self.assertIn(response.status_code, [404, 400])

    def test_sql_injection_in_comment_body(self):
        data = {
            "comment": "'; DROP TABLE product; --",
            "suggested": 1
        }
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_comment_with_long_text(self):
        long_comment = "عالی " * 200
        response = self.client.post(self.comment_url, {
            "comment": long_comment,
            "suggested": ProductComment.SUGGESTED
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("comment", response.data["errors"])  # exceeds max_length

    def test_post_comment_with_empty_comment(self):
        response = self.client.post(self.comment_url, {
            "comment": "",
            "suggested": ProductComment.NO_INFO
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("comment", response.data["errors"])

    def test_post_comment_with_invalid_suggested_value(self):
        response = self.client.post(self.comment_url, {
            "comment": "محصول خوبیه",
            "suggested": 999
        })
        self.assertEqual(response.status_code, 400)

    def test_get_comments_without_any_comment(self):
        response = self.client.get(self.comments_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_comment_and_rating_mapping(self):
        ProductComment.objects.create(
            comment="این نان بسیار خوشمزه بود",
            product=self.product,
            user=self.user,
            suggested=ProductComment.SUGGESTED
        )
        Rate.objects.create(
            product=self.product,
            rated_by=self.user,
            rate=4
        )
        response = self.client.get(self.comments_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["rating"], 4)
        self.assertEqual(response.data[0]["user_name"], self.user.username)
        self.assertIn("posted_at", response.data[0])


class ProductListViewsTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.product1 = Product.objects.create(
            category=self.category2,
            name="Bread A",
            price=Decimal("30.00"),
            description="Bread A desc",
            stock=5,
            box_type=1,

            color="Brown",
            discount=Decimal("5.00"),
            average_rate=Decimal("3.5"),
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name="Bread B",
            price=Decimal("40.00"),
            description="Bread B desc",
            stock=7,
            box_type=2,
            box_color="Red",
            color="Yellow",
            discount=Decimal("15.00"),
            average_rate=Decimal("4.8"),
        )
        self.product3 = Product.objects.create(
            category="taftoon",
            name="Bread C",
            price=Decimal("50.00"),
            description="Bread C desc",
            stock=3,
            box_type=2,

            color="Green",
            discount=Decimal("10.00"),
            average_rate=Decimal("4.0"),
        )

    def test_popular_product_view_status_and_order(self):
        url = reverse("popular-products")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        names_ordered = [item["name"] for item in response.data]
        self.assertEqual(names_ordered, ["Bread B", "Bread C", "Bread A"])

    def test_discount_product_view_status_and_order(self):
        url = reverse("discount-products")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        names_ordered = [item["name"] for item in response.data]
        self.assertEqual(names_ordered, ["Bread B", "Bread C", "Bread A"])

    def test_all_product_view_status_and_content(self):
        url = reverse("all-products")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        returned_names = {item["name"] for item in response.data}
        expected_names = {"Bread A", "Bread B", "Bread C"}
        self.assertSetEqual(returned_names, expected_names)

    def test_popular_view_empty(self):
        Product.objects.all().delete()
        url = reverse("popular-products")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_discount_view_empty(self):
        Product.objects.all().delete()
        url = reverse("discount-products")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_all_products_view_empty(self):
        Product.objects.all().delete()
        url = reverse("all-products")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_all_product_view_includes_new_product(self):
        new_product = Product.objects.create(
            category=self.category,
            name="Bread New",
            price=Decimal("60.00"),
            description="New product",
            stock=6,
            box_type=1,
            box_color="Green",
            color="White",
            discount=Decimal("8.00"),
            average_rate=Decimal("4.2"),
        )
        url = reverse("all-products")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data]
        self.assertIn("Bread New", names)

    def test_discount_view_with_zero_discount(self):
        product_zero_discount = Product.objects.create(
            category="taftoon",
            name="Bread Zero",
            price=Decimal("20.00"),
            description="No discount",
            stock=5,
            box_type=1,
            box_color="Gray",
            color="Black",
            discount=Decimal("0.00"),
            average_rate=Decimal("3.0"),
        )

        url = reverse("discount-products")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Bread Zero", [item["name"] for item in response.data])
        self.assertEqual(response.data[-1]["name"], "Bread Zero")

    def test_popular_view_with_equal_average_rates(self):
        self.product1.average_rate = Decimal("4.5")
        self.product2.average_rate = Decimal("4.5")
        self.product3.average_rate = Decimal("4.0")
        self.product1.save()
        self.product2.save()
        self.product3.save()

        url = reverse("popular-products")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        names_ordered = [item["name"] for item in response.data]
        self.assertIn("Bread A", names_ordered)
        self.assertIn("Bread B", names_ordered)
        self.assertIn("Bread C", names_ordered)
        self.assertEqual(len(response.data), 3)


class CategoryBoxViewTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        Product.objects.create(
            name="Test Bread 1",
            price=10000,
            stock=10,
            description="Test product",
            color="Brown",
            category=self.category,
            box_type=1,
        )

        Product.objects.create(
            name="Test Bread 2",
            price=12000,
            stock=5,
            description="Another test product",
            color="Golden",

            category=self.category,
            box_type=2,
        )
        self.url = reverse("category-box")

    def test_valid_request_returns_products(self):
        response = self.client.get(f"{self.url}?category=1&box_type=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_valid_request_with_no_matching_products(self):
        response = self.client.get(f"{self.url}?category=3&box_type=4")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_missing_parameters_returns_error(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_missing_category_returns_error(self):
        response = self.client.get(f"{self.url}?box_type=1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_missing_box_type_returns_error(self):
        response = self.client.get(f"{self.url}?category=1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_non_integer_category_returns_error(self):
        response = self.client.get(f"{self.url}?category=abc&box_type=1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_non_integer_box_type_returns_error(self):
        response = self.client.get(f"{self.url}?category=1&box_type=xyz")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_invalid_category_number_returns_error(self):
        response = self.client.get(f"{self.url}?category=99&box_type=1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_invalid_box_type_value_returns_error(self):
        response = self.client.get(f"{self.url}?category=1&box_type=3")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_multiple_matching_products(self):
        Product.objects.create(
            name="Another Bread",
            price=13000,
            stock=6,
            description="Second match",
            color="Light brown",

            category=self.category,
            box_type=1,
        )
        response = self.client.get(f"{self.url}?category=1&box_type=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_boundary_category_zero_returns_error(self):
        response = self.client.get(f"{self.url}?category=0&box_type=1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_boundary_category_seven_returns_error(self):
        response = self.client.get(f"{self.url}?category=7&box_type=1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
