from django.urls import path, include

app_name = 'accounts'

urlpatterns = [
    # Подключаем URL-маршруты из API
    path('', include('accounts.api.urls')),

    # В будущем здесь могут быть дополнительные URL-маршруты для не-API функций,
    # например, для HTML-страниц аутентификации, если потребуется
    # path('login/', views.login_view, name='login'),
    # path('logout/', views.logout_view, name='logout'),
    # и т.д.
]