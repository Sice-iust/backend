from locust import HttpUser, task, between
from random import randint, choice
from datetime import date, timedelta

# import random
# import string
# import json
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.contrib.auth import get_user_model
# User = get_user_model()
PRODUCT_IDS = [4,5,6,7,8,10,11,12,14,15,16]
from users.test_user import *
class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.register()
        self.rated_products = []
    def register(self):

        self.user = UserTest()
        self.user.setUp()
        self.token = self.user.access_token
        self.client.headers.update({"Authorization": f"Bearer {self.user.access_token}"})

        

    @task(2)
    def view_single_product(self):
        product_id = random.choice(PRODUCT_IDS)
        self.client.get(f"/product/{product_id}/")

    @task(3)
    def view_single_product_comments(self):
        product_id = random.choice(PRODUCT_IDS)
        self.client.get(f"/product/comments/{product_id}/")

    @task(10)
    def view_popular_products(self):
        self.client.get("/product/popular/")

    @task(10)
    def view_discounted_products(self):
        self.client.get("/product/discount/")

    @task(10)
    def view_all_products(self):
        self.client.get("/product/all/")

    @task(1)
    def rate_product(self):
        product_id = random.choice(list(set(PRODUCT_IDS).difference(set(self.rated_products))))
        self.rated_products.append(product_id)
        self.client.post(f"/user/rate/product/{product_id}/", json={"rate": randint(1, 5)})

    @task(1)
    def update_rating(self):
        self.rate_product()
        product_id = random.choice(self.rated_products)
        self.client.put(f"/user/rate/product/{product_id}/", json={"rate": randint(1, 5)})

    @task(1)
    def comment_on_product(self):
        product_id = random.choice(PRODUCT_IDS)

        self.client.post(f"/user/comment/product/{product_id}", json={
            "comment": "Great product!",
            "suggested": 3
        })

    @task(3)
    def view_category(self):
        category = choice([1, 2, 3, 4, 5, 6])
        self.client.get(f"/product/category/?category={category}")

    @task(3)
    def view_category_box(self):
        category = choice([1, 2, 3, 4, 5, 6])
        self.client.get(f"/product/category/?category={category}")

    
    @task(2)
    def get_profile(self):
        self.client.get("/users/profile/")

    # @task(5)
    # def update_profile(self):
    #     self.client.put("/users/profile/update/", json={
    # "username":"sample",
    # "profile_photo": "https://nanziback.liara.run/media/profiles/Default_pfp_qYtK61O.jpg"})

    @task(4)
    def get_my_location(self):
        self.post_location()
        self.client.get("/users/locations/mylocation/")

    @task(4)
    def post_location(self):
        payload = {
    "id": str(self.user.user.id),
    "user": {
        "username": str(self.user.username),
        "phonenumber": str(self.user.phonenumber)
            },
            "address": "",
            "name": "",
            "home_floor": 1,
            "home_unit": 1,
            "home_plaque": 1,
            "is_choose": "true"
        }
                
        res = self.client.post("/users/locations/mylocation/",json=payload)
        # print(res.text)
        data = res.json()
        self.location_id = data.get("id")
    @task(2)
    def choose_location(self):
        self.post_location()
        self.client.put(f"users/locations/choose/location/{self.location_id}")

    @task(5)
    def user_discounts(self):
        self.client.get("/user/discounts/")
    @task(3)
    def get_cart(self):
        self.cart = self.client.get(f'/user/cart/').json()
    @task(3)
    def add_to_cart(self):
        self.get_cart()
        ids = set([item['product']['id'] for item in self.cart['cart_items']])
        ids = set(PRODUCT_IDS).difference(ids)
        if ids:
            # print('ids',ids)
            id = random.choice(list(ids))
            self.client.post(f"/user/cart/creat/{id}/",json={"quantity": 1})
    @task(2)
    def user_order(self):
        self.client.get("/user/order/myorder/")

    @task(2)
    def delivery_slots(self):
        self.client.get("/user/delivery/")
    @task(2)
    def get_wallet(self):
        self.client.get("/user/wallet/")

    # @task(1)
    # def submit_order(self):
    #     today = date.today()
    #     tomorrow = today + timedelta(days=1)
    #     delivery_payload = [
    #         {
    #             "delivery_date": today.strftime("%Y-%m-%d"),
    #             "slots": [
    #                 {
    #                     "id": 12,
    #                     "day_name": "شنبه",
    #                     "start_time": "18:00:00",
    #                     "end_time": "20:00:00",
    #                     "delivery_date": "2025-06-07",
    #                     "max_orders": 100,
    #                     "current_fill": 0,
    #                     "shipping_fee": "250000.00"
    #                 },
    #                 {
    #                     "id": 13,
    #                     "day_name": "شنبه",
    #                     "start_time": "10:00:00",
    #                     "end_time": "12:00:00",
    #                     "delivery_date": "2025-06-07",
    #                     "max_orders": 100,
    #                     "current_fill": 0,
    #                     "shipping_fee": "25000.00"
    #                 },
    #                 {
    #                     "id": 14,
    #                     "day_name": "شنبه",
    #                     "start_time": "12:00:00",
    #                     "end_time": "14:00:00",
    #                     "delivery_date": "2025-06-07",
    #                     "max_orders": 1000,
    #                     "current_fill": 0,
    #                     "shipping_fee": "30000.00"
    #                 }
    #             ]
    #         },
    #         {
    #             "delivery_date": tomorrow.strftime("%Y-%m-%d"),
    #             "slots": [
    #                 {
    #                     "id": 15,
    #                     "day_name": "یک‌شنبه",
    #                     "start_time": "14:00:00",
    #                     "end_time": "16:00:00",
    #                     "delivery_date": "2025-06-08",
    #                     "max_orders": 199,
    #                     "current_fill": 1,
    #                     "shipping_fee": "30000.00"
    #                 }
    #             ]
    #         },

    #     ]

    #     self.add_to_cart(randint(1,14),3)
    #     self.client.post("/user/delivery/",json=delivery_payload)

    #     submit_payload = {
    #     "location_id": 1,
    #     "deliver_time": 10,
    #     "description": "good",
    #     "total_price": 27000,
    #     "profit": 3000,
    #     "total_payment": 24000,
    #     "discount_text": "Applied discount",
    #     "payment_status": "unpaid",
    #     "reciver": "مهسا",
    #     "reciver_phone": "989332328129"
    #     }
    #     self.client.post("/user/order/submit/", json=submit_payload)

    # @task(1)
    # def payment_verify(self):
    #     self.client.post("/api/payment/verify/", json={
    #         "Authority": "000000000000000000000000000000000000",
    #         "OrderId": 1
    #     })


    # @task
    # def admin_delivery_slots(self):
    #     self.client.get("/nanzi/admin/deliveryslot/")

    # @task
    # def single_admin_delivery_slot(self):
    #     self.client.get("/nanzi/admin/deliveryslot/1/")  # Change ID as needed

    # @task
    # def admin_delivered(self):
    #     self.client.get("/nanzi/admin/delivered/")

    # @task
    # def admin_processing(self):
    #     self.client.get("/nanzi/admin/process/")

    # @task
    # def admin_cancel(self):
    #     self.client.post("/nanzi/admin/cancle/", json={"order_id": 1})

    # @task
    # def change_status(self):
    #     self.client.post("/nanzi/status/change/1", json={"status": "delivered"})

    # @task
    # def order_id_lookup(self):
    #     self.client.get("/nanzi/admin/order/id/")

    # @task
    # def order_filter(self):
    #     self.client.post("/nanzi/admin/order/filter/", json={"status": "pending"})

    # @task
    # def admin_invoice(self):
    #     self.client.get("/nanzi/admin/order/invoice/1/")  # Change ID as needed

    # @task
    # def admin_archive(self):
        # self.client.get("/nanzi/admin/archive/")
  