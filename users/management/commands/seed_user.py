from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Comando para crear usuarios de prueba/semillas
class Command(BaseCommand):
    help = 'Siembra la base de datos con usuarios iniciales'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Usuarios de prueba
        test_users = [
            {
                'email': 'admin@ejemplo.com',
                'full_name': 'Usuario Admin',
                'password': 'admin123',
                'is_active': True,
                'is_staff': True
            },
            {
                'email': 'usuario@ejemplo.com',
                'full_name': 'Usuario Regular',
                'password': 'usuario123',
                'is_active': True
            }
        ]

        for user_data in test_users:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                email=user_data['email'], 
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario creado: {user.email}')
                )