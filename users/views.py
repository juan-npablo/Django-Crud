from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    LoginSerializer, 
    PasswordResetSerializer,
    PasswordConfirmResetSerializer,
    LogoutSerializer
)
from django.utils import timezone
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings

User = get_user_model()

#Vista de usuario con los métodos de creación, listado, actualización y eliminación
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    #Método para obtener los permisos de los usuarios
    def get_permissions(self):
        if self.action in ['create', 'login', 'reset_password', 'confirm_reset', 'confirm_password_reset']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    #Método para iniciar sesión
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
    #Método para cerrar sesión
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"mensaje": "Cierre de sesión exitoso"}, 
            status=status.HTTP_200_OK
        )

    #Método para restablecer la contraseña -> primero se envía un correo con un token
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"mensaje": "Enlace de restablecimiento de contraseña enviado a su correo"}, 
            status=status.HTTP_200_OK
        )

    #Este método se llama para confirmar que el token enviado en el correo es válido
    #-> segundo este token se envía junto con la nueva contraseña para restablecerla
    @action(detail=False, methods=['GET'], permission_classes=[AllowAny])
    def confirm_reset(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response(
                {"error": "Token no proporcionado"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar token
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:
            email = serializer.loads(token, salt='password-reset', max_age=3600)
            user = User.objects.get(email=email)
            
            # Validaciones adicionales
            if (user.reset_token != token or 
                user.reset_token_expires_at is None or 
                user.reset_token_expires_at < timezone.now()):
                return Response(
                    {"error": "Token inválido o expirado"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                "message": "Token válido. Puede proceder a cambiar su contraseña",
                "token": token
            }, status=status.HTTP_200_OK)
        
        except Exception:
            return Response(
                {"error": "Token inválido o expirado"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    #Método para confirmar el restablecimiento de la contraseña
    #-> tercero se envía la nueva contraseña para restablecerla con el token y la confirmación
    @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    def confirm_password_reset(self, request):
        serializer = PasswordConfirmResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"mensaje": "Contraseña restablecida exitosamente"}, 
            status=status.HTTP_200_OK
        )

    #Método para desactivar la cuenta de un usuario de forma permanente
    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def deactivate_account(self, request):
        # Obtener el usuario actual -> solo el propio usuario se puede desactivar la cuenta a sí mismo
        user = request.user
        user.is_active = False
        user.save()
        
        return Response({
            'detail': 'Cuenta desactivada exitosa y permanentemente',
            'user_id': user.id
        }, status=status.HTTP_200_OK)