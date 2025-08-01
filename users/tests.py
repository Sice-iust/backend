from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta
from .models import User, Otp
from .serializers import *
from .models import *
from django.test import TestCase,RequestFactory
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Otp,Location 
import datetime
from order.models import DiscountCart
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


User = get_user_model()

class LocationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fati",
            email="fati@example.com",
            phonenumber="+989123456789",
            password="securepass",
        )
        self.location = Location.objects.create(
            user=self.user,
            name="Home",
            address="123 Main Street",
            detail="Near park",
            home_plaque=42,
            home_unit=7,
            home_floor=3,
            is_choose=True,
        )

    def test_location_creation(self):
        self.assertEqual(self.location.name, "Home")
        self.assertTrue(self.location.is_choose)
        self.assertEqual(str(self.location), "Home - 123 Main Street")


class OtpModelTests(TestCase):
    def setUp(self):
        self.otp_entry = Otp.objects.create(phonenumber="+989111111111")

    def test_generate_otp_sets_fields(self):
        otp_value = self.otp_entry.generate_otp()
        self.assertEqual(self.otp_entry.otp, otp_value)
        self.assertTrue(self.otp_entry.otp_created_at <= timezone.now())

    def test_otp_validity_within_timeframe(self):
        self.otp_entry.generate_otp()
        self.assertTrue(self.otp_entry.is_otp_valid())

    def test_otp_expired(self):
        self.otp_entry.otp_created_at = timezone.now() - timedelta(minutes=5)
        self.otp_entry.save()
        self.assertFalse(self.otp_entry.is_otp_valid())


class CustomUserManagerTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="fati",
            email="fati@example.com",
            phonenumber="+989123456789",
            password="securepass",
        )
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.username, "fati")

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            phonenumber="+989987654321",
            password="adminpass",
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.username, "admin")

    def test_create_user_missing_fields(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username=None, email=None, phonenumber=None)


class SendOTPSerializerTest(TestCase):
    def test_valid_phonenumber(self):
        data = {"phonenumber": "1234567890"}
        serializer = SendOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["phonenumber"], "1234567890")


class OTPSerializersTest(TestCase):
    def test_login_verify_valid(self):
        data = {"phonenumber": "1234567890", "otp": "123456"}
        serializer = LoginVerifyOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_signup_verify_valid(self):
        data = {"phonenumber": "1234567890", "username": "fati", "otp": "654321"}
        serializer = SignUPVerifyOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_signup_missing_fields(self):
        serializer = SignUPVerifyOTPSerializer(
            data={"phonenumber": "123", "otp": "999999"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)


class LogOutSerializerTest(TestCase):
    def test_logout_valid(self):
        serializer = LogOutSerializer(data={"refresh_token": "sample_refresh_token"})
        self.assertTrue(serializer.is_valid())


class ProfileSerializerTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.user = User.objects.create_user(
            username="fati",
            password="pass123",
            email="fds@gmail.com",
            phonenumber="+98765432345",
        )

    def test_default_profile_photo(self):
        serializer = ProfileSerializer(
            instance=self.user, context={"request": self.request}
        )
        self.assertIn("profile_photo", serializer.data)
        self.assertTrue(serializer.data["profile_photo"].endswith("Default_pfp.jpg"))


class UpdateProfileSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fati",
            password="pass123",
            email="fds@gmail.com",
            phonenumber="+98765432345",
        )

    def test_update_username(self):
        serializer = UpdateProfileSerializer(
            instance=self.user, data={"username": "newname"}
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.username, "newname")


class LocationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fati", password="pass123",email="fds@gmail.com",phonenumber="+98765432345")
        self.location = Location.objects.create(
            user=self.user,
            address="123 Main St",
            name="Home",
            home_floor=2,
            home_unit=2,
            home_plaque=1,
            is_choose=True,
        )

    def test_location_serialization(self):
        serializer = LocationSerializer(instance=self.location)
        data = serializer.data
        self.assertEqual(data["name"], "Home")
        self.assertEqual(data["home_floor"], 2)
        self.assertEqual(data["is_choose"], True)


class SendOTPViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("send-otp")
        self.phone_number = "+989036635480"
        self.user = User.objects.create_user(
            phonenumber=self.phone_number,
            username="testuser",
            email="testuser@gmail.com",
            password="testuser1"
        )

    def test_send_otp_successfully(self):
        data = {"phonenumber": self.phone_number}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent")
        self.assertTrue(response.data["is_registered"])
        self.assertTrue(Otp.objects.filter(phonenumber=self.phone_number).exists())

    def test_send_otp_unregistered_user(self):
        data = {"phonenumber": "+989129876543"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent")
        self.assertFalse(response.data["is_registered"])
        self.assertTrue(Otp.objects.filter(phonenumber="+989129876543").exists())


    def test_invalid_phone_number(self):
        data = {"phonenumber": ""}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phonenumber", response.data)


class LoginVerifyOTPViewTest(APITestCase):
    def setUp(self):
        self.url = reverse("login")
        self.phonenumber = "+989123456789"
        self.user = User.objects.create_user(
            phonenumber=self.phonenumber, password="password123",username="usertest",
            email="testemail@gmail.com"
        )

    def create_otp(
        self, phonenumber=None, otp="123456", created_at=None, valid_minutes=5
    ):
        if created_at is None:
            created_at = timezone.now()
        otp_obj = Otp.objects.create(
            phonenumber=phonenumber or self.phonenumber,
            otp=otp,
            otp_created_at=created_at,
        )
        return otp_obj

    def test_login_successful(self):
        otp_obj = self.create_otp()
        data = {"phonenumber": self.phonenumber, "otp": otp_obj.otp}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertEqual(response.data["message"], "Login successful")
        self.assertFalse(Otp.objects.filter(phonenumber=self.phonenumber).exists())

    def test_user_not_registered(self):
        data = {"phonenumber": "+989999999999", "otp": "123456"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "you are not registered.")

    def test_otp_not_found(self):
        data = {"phonenumber": self.phonenumber, "otp": "123456"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP is used or expired.")

    def test_otp_expired(self):
        expired_time = timezone.now() - datetime.timedelta(minutes=10)
        otp_obj = self.create_otp(created_at=expired_time, valid_minutes=-5)
        data = {"phonenumber": self.phonenumber, "otp": otp_obj.otp}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP expired, request a new one.")

    def test_invalid_otp(self):
        otp_obj = self.create_otp(otp="111111")
        data = {"phonenumber": self.phonenumber, "otp": "999999"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "Invalid OTP.")

    def test_invalid_serializer_data(self):
        data = {
            "phonenumber": self.phonenumber,
        }
        response = self.client.post(self.url, data)
        self.assertIn("otp", response.data)

        data = {"phonenumber": "invalid-phone", "otp": "123456"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.data["message"], "you are not registered.")


class SignUpVerifyOTPViewTest(APITestCase):

    def setUp(self):
        self.url = reverse("signup")
        self.phonenumber = "+989123456789"
        self.username = "testuser"
        self.otp = "123456"
        self.otp_instance = Otp.objects.create(
            phonenumber=self.phonenumber, otp=self.otp, otp_created_at=timezone.now()
        )

    def test_successful_signup(self):
        data = {
            "phonenumber": self.phonenumber,
            "otp": self.otp,
            "username": self.username,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertTrue(User.objects.filter(phonenumber=self.phonenumber).exists())
        self.assertTrue(
            DiscountCart.objects.filter(user__phonenumber=self.phonenumber).exists()
        )

    def test_invalid_otp(self):
        data = {
            "phonenumber": self.phonenumber,
            "otp": "000000",
            "username": self.username,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )
        self.assertEqual(response.data, "Invalid OTP.")

    def test_expired_otp(self):
        self.otp_instance.otp_created_at = timezone.now() - timedelta(minutes=5)
        self.otp_instance.save()
        data = {
            "phonenumber": self.phonenumber,
            "otp": self.otp,
            "username": self.username,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP expired, request a new one.")

    def test_already_registered(self):
        User.objects.create(phonenumber=self.phonenumber, username="existing")
        data = {
            "phonenumber": self.phonenumber,
            "otp": self.otp,
            "username": self.username,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "this phone number is already registered."
        )

    def test_missing_otp_record(self):
        Otp.objects.all().delete()
        data = {
            "phonenumber": self.phonenumber,
            "otp": self.otp,
            "username": self.username,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP is used or expired.")


class UpdateProfileViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phonenumber="+989123456789", username="oldname", password="testpass123",email="fatemeh@gmail.com"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse(
            "update-profile"
        )

    def test_update_username(self):
        data = {"username": "newname"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newname")


class LogOutViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phonenumber="+989123456789", username="oldname", password="testpass123",email="fatemeh@gmail.com"
            )
        self.refresh = RefreshToken.for_user(self.user)
        self.access = self.refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        self.url = reverse("logout")

    def test_logout_successful(self):
        response = self.client.post(self.url, {"refresh_token": str(self.refresh)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Logged out successfully.")

    def test_logout_with_invalid_token(self):
        response = self.client.post(self.url, {"refresh_token": "invalidtoken"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], "Invalid or expired token.")

    def test_logout_without_token(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

class LocationViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phonenumber="+989123456789", username="testuser", password="pass",email="fatemeh@gmail.com"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("location")

    def test_create_location(self):
        data = {
            "name": "Home",
            "reciver": "Ali",
            "phonenumber": "+989876543210",
            "address": "Tehran, Vanak",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Home")

    def test_get_locations_empty(self):
        self.user2 = User.objects.create_user(
            phonenumber="+989128456789",
            username="testuser2",
            password="pass2",
            email="fatemeh2@gmail.com",
        )
        self.refresh = RefreshToken.for_user(self.user2)
        self.access = self.refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["error"], "You have not submitted any locations yet."
        )

    def test_get_locations_success(self):
        Location.objects.create(
            user=self.user,
            name="Home",
            reciver="Ali",
            phonenumber="09123456789",
            address="Tehran",
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access = self.refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Home")
def test_update_location_success(self):
    location = Location.objects.create(
        user=self.user,
        name="Home",
        reciver="Ali",
        phonenumber="+989123456789",
        address="Tehran",
    )
    self.refresh = RefreshToken.for_user(self.user)
    self.access = self.refresh.access_token
    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
    url = reverse("location-detail", args=[location.id])
    data = {"name": "New Home"}
    response = self.client.put(url, data, format="json")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["name"], "New Home")

def test_update_location_not_found(self):
    self.refresh = RefreshToken.for_user(self.user)
    self.access = self.refresh.access_token
    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
    url = reverse("location-detail", args=[999])
    data = {"name": "Updated Location"}
    response = self.client.put(url, data, format="json")

    self.assertEqual(response.status_code, 404)
    self.assertIn("error", response.data)
    self.assertEqual(response.data["error"], "Location not found or not owned by user.")

def test_delete_location_success(self):
    location = Location.objects.create(
        user=self.user,
        name="Home",
        reciver="Ali",
        phonenumber="09123456789",
        address="Tehran",
    )
    self.refresh = RefreshToken.for_user(self.user)
    self.access = self.refresh.access_token
    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
    url = reverse("location-detail", args=[location.id])
    response = self.client.delete(url)

    self.assertEqual(response.status_code, 204)
    self.assertEqual(response.data["message"], "Location deleted successfully.")

def test_delete_location_not_found(self):
    self.refresh = RefreshToken.for_user(self.user)
    self.access = self.refresh.access_token
    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
    url = reverse("location-detail", args=[999])
    response = self.client.delete(url)

    self.assertEqual(response.status_code, 404)
    self.assertIn("error", response.data)
    self.assertEqual(response.data["error"], "Location not found or not owned by user.")

class NeshanLocationViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phonenumber="+989123456789", username="testuser", password="testpass123",email="fatemeh@gmail.com"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("neshan-location")

    @patch(
        "users.views.reverse_geocode"
    )
    def test_valid_coordinates(self, mock_reverse_geocode):
        mock_reverse_geocode.return_value = {"address": "Tehran, Iran"}
        response = self.client.get(self.url, {"lat": 35.6892, "lng": 51.3890})

        self.assertEqual(response.status_code, 200)
        self.assertIn("address", response.data)

    def test_missing_lat(self):
        response = self.client.get(self.url, {"lng": 51.3890})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "lng and lat are required")

    def test_missing_lng(self):
        response = self.client.get(self.url, {"lat": 35.6892})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "lng and lat are required")

    def test_invalid_lat_lng_format(self):
        response = self.client.get(self.url, {"lat": "invalid", "lng": "text"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "lng and lat must be floats")

    @patch("users.views.reverse_geocode")
    def test_neshan_api_returns_empty(self, mock_reverse_geocode):
        mock_reverse_geocode.return_value = None
        response = self.client.get(self.url, {"lat": 35.6892, "lng": 51.3890})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Neshan API returned no data")

    @patch("users.views.reverse_geocode")
    def test_neshan_api_raises_exception(self, mock_reverse_geocode):
        mock_reverse_geocode.side_effect = Exception("Timeout error")
        response = self.client.get(self.url, {"lat": 35.6892, "lng": 51.3890})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.data)
        self.assertIn("Neshan API failed", response.data["error"])

    def test_unauthenticated_user(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {"lat": 35.6892, "lng": 51.3890})
        self.assertEqual(response.status_code, 401)


class ChooseLocationViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phonenumber="+989123456789",
            username="testuser",
            password="pass",
            email="fatemeh@gmail.com",
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access = self.refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        self.location1 = Location.objects.create(
            user=self.user,
            name="Home",
            reciver="Ali",
            phonenumber="09123456789",
            address="Tehran",
            is_choose=False,
        )
        self.location2 = Location.objects.create(
            user=self.user,
            name="Work",
            reciver="Sara",
            phonenumber="09129876543",
            address="Karaj",
            is_choose=True,
        )
        self.url = reverse("choose-location", args=[self.location1.id])

    def test_choose_location_success(self):
        response = self.client.put(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], "Location successfully chosen.")

        self.location1.refresh_from_db()
        self.location2.refresh_from_db()

        self.assertTrue(self.location1.is_choose)
        self.assertFalse(self.location2.is_choose)

    def test_choose_location_not_found_or_unauthorized(self):

        other_user = User.objects.create_user(
            phonenumber="+989111111111",
            username="otheruser",
            password="pass2",
            email="other@gmail.com",
        )
        other_location = Location.objects.create(
            user=other_user,
            name="Other",
            reciver="Reza",
            phonenumber="09120000000",
            address="Shiraz",
            is_choose=False,
        )

        url = reverse("choose-location", args=[other_location.id])
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(
            response.data["error"], "Location not found or not owned by user."
        )

    def test_unauthenticated_user(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
