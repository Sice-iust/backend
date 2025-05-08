from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from .models import Product, Subcategory,Rate
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import tempfile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# class ProductAPITestCase(APITestCase):
#     def setUp(self):

#         self.product = Product.objects.create(
#             category="barbari",
#             name="Test Product",
#             price=Decimal("100.00"),
#             description="Test Description",
#             stock=10,
#             box_type=2,
#             box_color="Red",
#             color="Blue",
#             discount=Decimal(10),
#         )
#         Subcategory.objects.create(product=self.product, subcategory="Fresh")
#         self.url = reverse("product-list")

#     def _generate_image(self):
#         image = Image.new("RGB", (100, 100))
#         tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
#         image.save(tmp_file, format="JPEG")
#         tmp_file.seek(0)
#         return SimpleUploadedFile(
#             "test.jpg", tmp_file.read(), content_type="image/jpeg"
#         )

#     def test_get_all_products(self):
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("context", response.data)
#         self.assertEqual(len(response.data["context"]), 1)

#     def test_discounted_price_calculated_correctly(self):
#         response = self.client.get(self.url)
#         data = response.data["context"][0]
#         expected_price = Decimal(self.product.price * (1 - self.product.discount / 100))
#         self.assertEqual(data["discounted_price"], expected_price)

#     def test_photo_url_is_generated(self):
#         image = self._generate_image()
#         product_with_photo = Product.objects.create(
#             category="barbari",
#             name="Photo Product",
#             price=Decimal("150.00"),
#             description="Has photo",
#             stock=3,
#             box_type=3,
#             box_color="White",
#             color="Orange",
#             discount=5,
#             photo=image,
#         )
#         response = self.client.get(self.url)
#         product_data = [
#             p for p in response.data["context"] if p["name"] == "Photo Product"
#         ][0]
#         self.assertTrue(product_data["photo_url"].startswith("http"))

#     def test_create_product_with_subcategories_no_post(self):
#         image = self._generate_image()
#         data = {
#             "category": "barbari",
#             "name": "New Product",
#             "price": "200.00",
#             "description": "Description here",
#             "stock": 5,
#             "box_type": 3,
#             "box_color": "Green",
#             "color": "Yellow",
#             "discount": 15,
#             "photo": image,
#             "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
#         }
#         response = self.client.post(self.url, data, format="multipart")
#         self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
#         self.assertEqual(
#             Subcategory.objects.filter(product__name="New Product").count(), 0
#         )


# class PostProductAPITestCase(APITestCase):
#     def setUp(self):

#         self.product = Product.objects.create(
#             category="barbari",
#             name="Test Product",
#             price=Decimal("100.00"),
#             description="Test Description",
#             stock=10,
#             box_type=2,
#             box_color="Red",
#             color="Blue",
#             discount=Decimal(10),
#         )
#         Subcategory.objects.create(product=self.product, subcategory="Fresh")
#         self.url = reverse("product-post")

#     def _generate_image(self):
#         image = Image.new("RGB", (100, 100))
#         tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
#         image.save(tmp_file, format="JPEG")
#         tmp_file.seek(0)
#         return SimpleUploadedFile(
#             "test.jpg", tmp_file.read(), content_type="image/jpeg"
#         )

#     def test_create_product_with_subcategories_no_admin(self):
#         self.user = User.objects.create_user(
#             username="testuser",
#             password="testpass",
#             email="fati@gmail.com",
#             phonenumber="+989034488755"
#         )
#         admin_group, _ = Group.objects.get_or_create(name="Admin")
#         # self.user.groups.add(admin_group)
#         refresh = RefreshToken.for_user(self.user)
#         access_token = str(refresh.access_token)
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
#         image = self._generate_image()
#         data = {
#             "category": "barbari",
#             "name": "New Product",
#             "price": "200.00",
#             "description": "Description here",
#             "stock": 5,
#             "box_type": 3,
#             "box_color": "Green",
#             "color": "Yellow",
#             "discount": 15,
#             "photo": image,
#             "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
#         }
#         response = self.client.post(self.url, data, format="multipart")
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(response.data["message"], "Permission denied")

#     def test_create_product_with_subcategories_no_box(self):
#         self.user = User.objects.create_user(
#             username="testuser",
#             password="testpass",
#             email="fati@gmail.com",
#             phonenumber="+989034488755",
#         )
#         admin_group, _ = Group.objects.get_or_create(name="Admin")
#         self.user.groups.add(admin_group)
#         refresh = RefreshToken.for_user(self.user)
#         access_token = str(refresh.access_token)
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

#         image = self._generate_image()
#         data = {
#             "category": "barbari",
#             "name": "New Product",
#             "price": Decimal(200.00),
#             "description": "Description here",
#             "stock": 5,
#             "box_type": 3,
#             "box_color": "Green",
#             "color": "Yellow",
#             "discount": 15,
#             "photo": image,
#             "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
#         }

#         response = self.client.post(self.url, data, format="multipart")

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_create_product_with_subcategories(self):
#         self.user = User.objects.create_user(
#             username="testuser",
#             password="testpass",
#             email="fati@gmail.com",
#             phonenumber="+989034488755",
#         )
#         admin_group, _ = Group.objects.get_or_create(name="Admin")
#         self.user.groups.add(admin_group)
#         refresh = RefreshToken.for_user(self.user)
#         access_token = str(refresh.access_token)
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

#         image = self._generate_image()
#         data = {
#             "category": "barbari",
#             "name": "New Product",
#             "price": Decimal(200.00),
#             "description": "Description here",
#             "stock": 5,
#             "box_type": 4,
#             "box_color": "Green",
#             "color": "Yellow",
#             "discount": 15,
#             "photo": image,
#             "subcategories": [{"subcategory": "Hot"}, {"subcategory": "Fresh"}],
#         }

#         response = self.client.post(self.url, data, format="multipart")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["message"], "Product saved successfully")
#         product = Product.objects.get(name="New Product")
#         self.assertEqual(product.name, "New Product")
#         self.assertEqual(product.category, "barbari")
#         self.assertEqual(Decimal(product.price), Decimal(200.00))

#     def test_create_product_missing_required_fields(self):
#         self.user = User.objects.create_user(
#             username="testuser",
#             password="testpass",
#             email="fati@gmail.com",
#             phonenumber="+989034488755",
#         )
#         admin_group, _ = Group.objects.get_or_create(name="Admin")
#         self.user.groups.add(admin_group)
#         refresh = RefreshToken.for_user(self.user)
#         access_token = str(refresh.access_token)
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
#         data = {
#             "category":"barbari",
#             "name": "",
#             "price": "",
#         }
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

# class SingleProductAPITestCase(APITestCase):
#     def setUp(self):

#         self.product = Product.objects.create(
#             category="barbari",
#             name="Test Product",
#             price=Decimal("100.00"),
#             description="Test Description",
#             stock=10,
#             box_type=2,
#             box_color="Red",
#             color="Blue",
#             discount=Decimal(10),
#         )
#         Subcategory.objects.create(product=self.product, subcategory="Fresh")
#         self.url = reverse("product-single",args=[self.product.id])
#     def _generate_image(self):
#         image = Image.new("RGB", (100, 100))
#         tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
#         image.save(tmp_file, format="JPEG")
#         tmp_file.seek(0)
#         return SimpleUploadedFile(
#             "test.jpg", tmp_file.read(), content_type="image/jpeg"
#         )
#     def test_get_single_product_success(self):
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["name"], "Test Product")
#         self.assertEqual(
#             response.data["category"], "barbari"
#         )
#         self.assertEqual(Decimal(response.data["price"]), Decimal("100.00"))
#         self.assertEqual(response.data["stock"], 10)
#         self.assertEqual(response.data["discount"], 10)

#         subcategories = [sub["subcategory"] for sub in response.data["subcategories"]]
#         self.assertIn("Fresh", subcategories)

#     def test_get_single_product_not_found(self):
#         invalid_id = self.product.id + 55
#         url = reverse("product-single", args=[invalid_id])
#         response = self.client.get(url)

#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertEqual(response.data["message"], "Product not found")


# class AdminSingleProductAPITestCase(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username="adminuser",
#             password="adminpass",
#             email="admin@example.com",
#             phonenumber="+989034488755",
#         )
#         admin_group, _ = Group.objects.get_or_create(name="Admin")
#         self.user.groups.add(admin_group)
#         refresh = RefreshToken.for_user(self.user)
#         access_token = str(refresh.access_token)
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

#         self.product = Product.objects.create(
#             category="barbari",
#             name="Test Product",
#             price=Decimal("100.00"),
#             description="Test Description",
#             stock=10,
#             box_type=2,
#             box_color="Red",
#             color="Blue",
#             discount=Decimal(10),
#         )
#         self.url = reverse("admin-product-single", args=[self.product.id])
#         self.invalid_url = reverse("admin-product-single", args=[9999])

#     def test_update_product_success(self):
#         data = {
#             "name": "Updated Product",
#             "price": "120.00",
#             "stock": 15,
#         }
#         response = self.client.put(self.url, data)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["message"], "Product updated successfully")
#         self.product.refresh_from_db()
#         self.assertEqual(self.product.name, "Updated Product")
#         self.assertEqual(self.product.price, Decimal("120.00"))
#         self.assertEqual(self.product.stock, 15)

#     def test_update_product_not_found(self):
#         data = {
#             "name": "Not Found",
#         }
#         response = self.client.put(self.invalid_url, data)
#         self.assertEqual(response.status_code, 404)

#     def test_delete_product_success(self):
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["message"], "Product deleted successfully")
#         self.assertFalse(Product.objects.filter(id=self.product.id).exists())

#     def test_delete_product_not_found(self):
#         response = self.client.delete(self.invalid_url)
#         self.assertEqual(response.status_code, 404)
#         self.assertEqual(response.data["message"], "Product not found")

#     def test_update_permission_denied(self):
#         self.user.groups.clear()
#         data = {"name": "Hack Attempt"}
#         response = self.client.put(self.url, data)
#         self.assertEqual(response.status_code, 403)
#         self.assertEqual(response.data["message"], "Permission denied")

#     def test_delete_permission_denied(self):
#         self.user.groups.clear()
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, 403)
#         self.assertEqual(response.data["message"], "Permission denied")


# class RateViewAPITestCase(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username="adminuser",
#             password="adminpass",
#             email="admin@example.com",
#             phonenumber="+989034488755",
#         )
#         self.user2 = User.objects.create_user(
#             username="adminuser2",
#             password="adminpass2",
#             email="admin2@example.com",
#             phonenumber="+989034488752",
#         )
#         self.product = Product.objects.create(
#             category="sangak",
#             name="Sample Product",
#             price=Decimal("50.00"),
#             description="A great bread",
#             stock=20,
#             box_type=1,
#             box_color="White",
#             color="Brown",
#             discount=Decimal(5),
#         )

#         self.rate1 = Rate.objects.create(product=self.product, rate=Decimal("4.5"),rated_by=self.user)
#         self.rate2 = Rate.objects.create(product=self.product, rate=Decimal("3.8"),rated_by=self.user2)

#         self.url = reverse("rate-view")

#     def test_get_rate_list(self):
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn("context", response.data)
#         self.assertEqual(len(response.data["context"]), 2)

#         rate_data = response.data["context"][0]
#         self.assertIn("product", rate_data)
#         self.assertIn("rate", rate_data)
#         self.assertEqual(Decimal(rate_data["rate"]), Decimal("4.5"))


# class SingleRateViewAPITestCase(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username="adminuser",
#             password="adminpass",
#             email="admin@example.com",
#             phonenumber="+989034488755",
#         )

#         admin_group, _ = Group.objects.get_or_create(name="Admin")
#         self.user.groups.add(admin_group)

#         self.product = Product.objects.create(
#             category="sangak",
#             name="Sample Product",
#             price=Decimal("50.00"),
#             description="A great bread",
#             stock=20,
#             box_type=1,
#             box_color="White",
#             color="Brown",
#             discount=Decimal(5),
#         )

#         self.url = reverse("rate-add", kwargs={"id": self.product.id})

#         refresh = RefreshToken.for_user(self.user)
#         self.access_token = str(refresh.access_token)
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

#     def test_post_create_rating(self):
#         response = self.client.post(self.url, {"rate": "4.5"}, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Rate.objects.count(), 1)
#         self.assertEqual(Rate.objects.first().rate, Decimal("4.5"))

#     def test_post_duplicate_rating(self):
#         Rate.objects.create(
#             product=self.product, rate=Decimal("3.5"), rated_by=self.user
#         )
#         response = self.client.post(self.url, {"rate": "4.5"}, format="json")
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_put_update_rating(self):
#         Rate.objects.create(
#             product=self.product, rate=Decimal("3.0"), rated_by=self.user
#         )
#         response = self.client.put(self.url, {"rate": "4.7"}, format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.product.refresh_from_db()
#         self.assertEqual(float(self.product.average_rate), 4.7)

#     def test_delete_rating(self):
#         Rate.objects.create(
#             product=self.product, rate=Decimal("4.0"), rated_by=self.user
#         )
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(Rate.objects.count(), 0)

#     def test_unauthorized_access(self):
#         self.client.credentials()
#         response = self.client.post(self.url, {"rate": "5"}, format="json")
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProductViewsTestCase(APITestCase):
    def setUp(self):
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
        self.product1 = Product.objects.create(
            category="sangak",
            name="Bread A",
            price=Decimal("50.00"),
            description="Good bread",
            stock=10,
            box_type=1,
            box_color="Red",
            color="Brown",
            discount=Decimal("5"),
            average_rate=4.5,
        )
        self.product2 = Product.objects.create(
            category="barbari",
            name="Bread B",
            price=Decimal("60.00"),
            description="Better bread",
            stock=5,
            box_type=1,
            box_color="Blue",
            color="Golden",
            discount=Decimal("10"),
            average_rate=3.5,
        )

        Subcategory.objects.create(product=self.product1, subcategory="traditional")
        Subcategory.objects.create(product=self.product2, subcategory="crispy")

        self.popular_url = reverse("popular-product")  
        self.discount_url = reverse("discount-product") 

    def test_popular_products(self):
        response = self.client.get(self.popular_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertGreaterEqual(
            response.data[0]["average_rate"], response.data[1]["average_rate"]
        )

    def test_discounted_products(self):
        response = self.client.get(self.discount_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertGreaterEqual(
            response.data[0]["discount"], response.data[1]["discount"]
        )
        self.assertIn("discounted_price", response.data[0])
        self.assertIn(
            "photo_url", response.data[0]
        )  