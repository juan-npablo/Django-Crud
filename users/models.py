from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import bcrypt

#Modelo de usuario personalizado con 
#Nombre completo
#Correo electrónico
#Fecha de creación
#contraseña cifrada
#Activo
#Y campos para restablecimiento de contraseña
class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, is_active=True):
        if not email:
            raise ValueError('Los usuarios deben tener un correo electrónico')
        
        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            is_active=is_active
        )
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user

    #En caso de que se desee crear un super usuario
    def create_superuser(self, email, full_name, password):
        user = self.create_user(
            email=email,
            full_name=full_name,
            password=password,
            is_active=True
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

#Modelo de usuario personalizado con la especificación de los campos y su tipo de dato
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    date_created = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Nuevos campos para restablecimiento de contraseña
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token_expires_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

    #Métodos para cifrar y comparar contraseñas
    def set_password(self, raw_password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), salt)
        self.password = hashed.decode('utf-8')

    def check_password(self, raw_password):
        return bcrypt.checkpw(
            raw_password.encode('utf-8'), 
            self.password.encode('utf-8')
        )