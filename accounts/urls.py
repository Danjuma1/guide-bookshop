from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add, name='staff_add'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    path('profile/', views.profile_view, name='profile'),
]
