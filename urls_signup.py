from django.urls import path
import views_signup

urlpatterns = [
    path('', views_signup.signup_country_select, name='signup_country_select'),
    path('chile/', views_signup.signup_chile, name='signup_chile'),
    path('usa/', views_signup.signup_usa, name='signup_usa'),
]
