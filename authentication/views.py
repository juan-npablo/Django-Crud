from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

#Vista personalizada para manejar la autenticación
class CustomAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Método personalizado para manejar autenticación"""
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({
                'error': 'Contraseña incorrecta'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                'error': 'Cuenta de usuario inactiva'
            }, status=status.HTTP_403_FORBIDDEN)

        # Generar tokens de acceso y refresco
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name
            }
        }, status=status.HTTP_200_OK)