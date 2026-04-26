from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, ValueError):
        return Response(
            {
                'success': False,
                'errors': {'detail': str(exc)},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, PermissionError):
        return Response(
            {
                'success': False,
                'errors': {'detail': str(exc)},
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'success': False,
            'errors': response.data,
        }
    return response
