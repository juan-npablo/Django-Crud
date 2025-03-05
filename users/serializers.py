from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from itsdangerous import URLSafeTimedSerializer

User = get_user_model()

# Serializador de usuario
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'date_created', 'is_active']
        read_only_fields = ['id', 'date_created']

# Serializador de creación de usuario
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'is_active']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=password,
            is_active=validated_data.get('is_active', True)
        )
        return user

# Serializador de inicio de sesión del usuario
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Credenciales inválidas")

        if not user.is_active:
            raise serializers.ValidationError("Cuenta de usuario inactiva")

        if not user.check_password(password):
            raise serializers.ValidationError("Credenciales inválidas")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }

# Serializador de cierre de sesión del usuario
# En el header y en el body de la petición se debe enviar el token de autenticación 
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh_token']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError("Token inválido o ya fue invalidado")
        
#Serializador de restablecimiento de contraseña
#Como no se ha desplegado la aplicación genera un link de restablecimiento de contraseña
#El cual es enviado a través del correo electrónico utilizando la función send_mail
#Con ayuda de las contraseñas de terceros de google
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No existe un usuario con este correo electrónico")
        return email

    def create(self, validated_data):
        email = validated_data['email']
        user = User.objects.get(email=email)

        # Generar token seguro
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        token = serializer.dumps(user.email, salt='password-reset')

        # Guardar token en el usuario
        user.reset_token = token
        user.reset_token_expires_at = timezone.now() + timezone.timedelta(hours=1)
        user.save()

        # Generar enlace de restablecimiento
        reset_url = f"http://localhost:8000/api/users/confirm_reset/?token={token}"

        # Envío de correo con send_mail
        try:
            send_mail(
                'Restablecimiento de Contraseña',
                f'Haz clic en el siguiente enlace para restablecer tu contraseña: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=f"""
                <h1>Restablecimiento de Contraseña</h1>
                <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
                <a href="{reset_url}">Restablecer Contraseña</a>
                <p>Este enlace expirará en 1 hora.</p>
                """
            )
        except Exception as e:
            raise serializers.ValidationError(f"Error enviando correo: {str(e)}")

        return validated_data
    
#Serializador de confirmación de restablecimiento de contraseña    
class PasswordConfirmResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        token = validated_data['token']
        new_password = validated_data['new_password']

        # Validar token
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:
            email = serializer.loads(token, salt='password-reset', max_age=3600)
        except Exception:
            raise serializers.ValidationError("Token inválido o expirado")

        # Obtener usuario
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")

        # Validar token guardado (opcional)
        if user.reset_token != token or user.reset_token_expires_at < timezone.now():
            raise serializers.ValidationError("Token expirado")

        # Cambiar contraseña
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        user.save()

        return validated_data