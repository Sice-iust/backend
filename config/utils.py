from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    TokenError,
    AuthenticationFailed as JWTAuthFailed,
)
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    if isinstance(exc, (InvalidToken, TokenError, JWTAuthFailed)):
        return Response(
            {"detail": "Token is invalid or expired.", "is_login": False},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    response = exception_handler(exc, context)
    return response
