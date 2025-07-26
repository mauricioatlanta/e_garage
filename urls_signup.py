from django.urls import path
from . import views_signup

urlpatterns = [
    path('signup/', views_signup.signup_country_select, name='signup_country_select'),
    path('signup/chile/', views_signup.signup_chile, name='signup_chile'),
    path('signup/usa/', views_signup.signup_usa, name='signup_usa'),
]
