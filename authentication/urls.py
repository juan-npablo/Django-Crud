from django.urls import path
from .views import CustomAuthView

urlpatterns = [
    path('login/', CustomAuthView.as_view(), name='custom_login'),
]