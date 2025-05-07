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

