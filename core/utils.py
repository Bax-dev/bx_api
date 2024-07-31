from rest_framework.response import Response

def standard_response(success=True, message=None, data=None, status=200):
    return Response({
        'success': success,
        'message': message,
        'data': data
    }, status=status)




