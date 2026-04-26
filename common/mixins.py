from rest_framework.response import Response


class StandardResponseMixin:
    def success_response(self, data=None, message='Success', status_code=200):
        return Response({'success': True, 'message': message, 'data': data}, status=status_code)
