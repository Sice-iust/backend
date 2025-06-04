from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response


class RateTimeClass:
    ratelimit_key = "ip"
    ratelimit_rate = "10/m"
    ratelimit_block = True
    methods_to_limit = ["post"] 

    @classmethod
    def decorate(cls, view_cls):
        for method_name in cls.methods_to_limit:
            if hasattr(view_cls, method_name):
                method = getattr(view_cls, method_name)
                decorated_method = method_decorator(
                    ratelimit(
                        key=cls.ratelimit_key,
                        rate=cls.ratelimit_rate,
                        block=cls.ratelimit_block,
                    )
                )(method)
                setattr(view_cls, method_name, decorated_method)
        return view_cls

class ThreePerMinuteLimit(RateTimeClass):
    ratelimit_rate = "3/m"
    methods_to_limit = ["post"]


class GetAndPostLimit(RateTimeClass):
    ratelimit_rate = "5/m"
    methods_to_limit = ["get", "post","put"]  


class GetOnlyLimit(RateTimeClass):
    ratelimit_rate = "2/m"
    methods_to_limit = ["get"]  


class RateTimeBaseView:
    ratetime_class = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for limiter_cls in getattr(cls, "ratetime_class", []):
            limiter_cls.decorate(cls)
