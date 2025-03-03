import requests
import json
import logging
from abc import ABC, abstractmethod
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseOAuthAdapter(ABC):
    """
    Базовый класс для адаптеров OAuth.
    Определяет общий интерфейс для всех адаптеров.
    """
    provider_name = None  # Имя провайдера OAuth, должно быть переопределено в подклассах

    @abstractmethod
    def get_auth_url(self, redirect_uri, state=None):
        """
        Возвращает URL для начала процесса OAuth авторизации.

        Args:
            redirect_uri (str): URI для перенаправления после авторизации
            state (str, optional): Параметр состояния для предотвращения CSRF-атак

        Returns:
            str: URL для авторизации
        """
        pass

    @abstractmethod
    def exchange_code_for_token(self, code, redirect_uri):
        """
        Обменивает код авторизации на токен доступа.

        Args:
            code (str): Код авторизации, полученный от OAuth провайдера
            redirect_uri (str): URI перенаправления, который использовался при авторизации

        Returns:
            dict: Словарь с токенами доступа и обновления
        """
        pass

    @abstractmethod
    def get_user_info(self, access_token):
        """
        Получает информацию о пользователе с использованием токена доступа.

        Args:
            access_token (str): Токен доступа

        Returns:
            dict: Информация о пользователе
        """
        pass

    def process_user_data(self, user_data):
        """
        Преобразует полученные данные пользователя в стандартный формат.

        Args:
            user_data (dict): Данные пользователя от OAuth провайдера

        Returns:
            dict: Стандартизированные данные пользователя
        """
        # Базовая реализация, должна быть переопределена в подклассах
        return {
            'provider': self.provider_name,
            'provider_user_id': str(user_data.get('id')),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'avatar_url': user_data.get('avatar_url', None),
            'raw_data': user_data
        }

    def get_or_create_user(self, user_data):
        """
        Получает или создает пользователя на основе данных от OAuth провайдера.

        Args:
            user_data (dict): Стандартизированные данные пользователя

        Returns:
            tuple: (user, created) - пользователь и флаг, был ли он создан
        """
        email = user_data.get('email')

        if not email:
            raise ValueError(_("Не удалось получить email пользователя от OAuth провайдера"))

        try:
            # Ищем пользователя по email
            user = User.objects.get(email=email)
            created = False

            # Обновляем данные пользователя, если они изменились
            if not user.first_name and user_data.get('first_name'):
                user.first_name = user_data.get('first_name')

            if not user.last_name and user_data.get('last_name'):
                user.last_name = user_data.get('last_name')

            user.save()

        except User.DoesNotExist:
            # Создаем нового пользователя
            username_base = email.split('@')[0]
            username = username_base

            # Если имя пользователя занято, добавляем суффикс
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}_{suffix}"
                suffix += 1

            # Создаем пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                # Устанавливаем случайный пароль, который пользователь не сможет использовать
                password=User.objects.make_random_password()
            )
            created = True

            # Обновляем профиль пользователя, если у него есть аватар
            if hasattr(user, 'profile') and user_data.get('avatar_url'):
                try:
                    from django.core.files.base import ContentFile
                    import urllib.request

                    # Скачиваем аватар
                    avatar_url = user_data.get('avatar_url')
                    response = urllib.request.urlopen(avatar_url)

                    # Сохраняем в профиль
                    user.profile.avatar.save(
                        f"{username}_avatar.jpg",
                        ContentFile(response.read()),
                        save=True
                    )
                except Exception as e:
                    logger.error(f"Ошибка при загрузке аватара для пользователя {username}: {e}")

        # Сохраняем связь пользователя с OAuth провайдером
        self._save_oauth_connection(user, user_data)

        return user, created

    def _save_oauth_connection(self, user, user_data):
        """
        Сохраняет связь между пользователем и OAuth провайдером.

        Args:
            user (User): Пользователь
            user_data (dict): Данные пользователя от OAuth провайдера
        """
        # Проверяем наличие модели SocialAccount
        try:
            from accounts.models.social_account import SocialAccount

            # Получаем или создаем запись о связи
            social_account, created = SocialAccount.objects.get_or_create(
                user=user,
                provider=self.provider_name,
                provider_user_id=user_data.get('provider_user_id'),
                defaults={
                    'email': user_data.get('email'),
                    'extra_data': json.dumps(user_data.get('raw_data', {}))
                }
            )

            # Обновляем данные, если запись уже существовала
            if not created:
                social_account.email = user_data.get('email')
                social_account.extra_data = json.dumps(user_data.get('raw_data', {}))
                social_account.save()

        except (ImportError, ModuleNotFoundError):
            # Модель SocialAccount не найдена, логируем предупреждение
            logger.warning("Модель SocialAccount не найдена. Связь с OAuth провайдером не сохранена.")
            pass
        except Exception as e:
            logger.error(f"Ошибка при сохранении связи с OAuth провайдером: {e}")


class GoogleOAuthAdapter(BaseOAuthAdapter):
    """
    Адаптер для интеграции с Google OAuth 2.0.
    """
    provider_name = 'google'

    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', None)

        if not self.client_id or not self.client_secret:
            logger.warning("GOOGLE_OAUTH_CLIENT_ID или GOOGLE_OAUTH_CLIENT_SECRET не настроены")

    def get_auth_url(self, redirect_uri, state=None):
        """
        Возвращает URL для авторизации через Google.
        """
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'email profile',
            'access_type': 'offline',
            'include_granted_scopes': 'true',
        }

        if state:
            params['state'] = state

        # Формируем URL с параметрами
        auth_url = f"{base_url}?"
        auth_url += "&".join([f"{key}={value}" for key, value in params.items()])

        return auth_url

    def exchange_code_for_token(self, code, redirect_uri):
        """
        Обменивает код авторизации на токен доступа.
        """
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Ошибка при обмене кода на токен: {response.status_code} - {response.text}")
            raise Exception(_("Не удалось обменять код авторизации на токен доступа"))

        return response.json()

    def get_user_info(self, access_token):
        """
        Получает информацию о пользователе от Google.
        """
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {
            'Authorization': f"Bearer {access_token}"
        }

        response = requests.get(user_info_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Ошибка при получении информации о пользователе: {response.status_code} - {response.text}")
            raise Exception(_("Не удалось получить информацию о пользователе"))

        return response.json()

    def process_user_data(self, user_data):
        """
        Преобразует данные пользователя от Google в стандартный формат.
        """
        return {
            'provider': self.provider_name,
            'provider_user_id': user_data.get('sub'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'first_name': user_data.get('given_name', ''),
            'last_name': user_data.get('family_name', ''),
            'avatar_url': user_data.get('picture'),
            'raw_data': user_data
        }


class YandexOAuthAdapter(BaseOAuthAdapter):
    """
    Адаптер для интеграции с Яндекс OAuth.
    """
    provider_name = 'yandex'

    def __init__(self):
        self.client_id = getattr(settings, 'YANDEX_OAUTH_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'YANDEX_OAUTH_CLIENT_SECRET', None)

        if not self.client_id or not self.client_secret:
            logger.warning("YANDEX_OAUTH_CLIENT_ID или YANDEX_OAUTH_CLIENT_SECRET не настроены")

    def get_auth_url(self, redirect_uri, state=None):
        """
        Возвращает URL для авторизации через Яндекс.
        """
        base_url = "https://oauth.yandex.ru/authorize"
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'login:email login:info',
        }

        if state:
            params['state'] = state

        # Формируем URL с параметрами
        auth_url = f"{base_url}?"
        auth_url += "&".join([f"{key}={value}" for key, value in params.items()])

        return auth_url

    def exchange_code_for_token(self, code, redirect_uri):
        """
        Обменивает код авторизации на токен доступа.
        """
        token_url = "https://oauth.yandex.ru/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Ошибка при обмене кода на токен: {response.status_code} - {response.text}")
            raise Exception(_("Не удалось обменять код авторизации на токен доступа"))

        return response.json()

    def get_user_info(self, access_token):
        """
        Получает информацию о пользователе от Яндекса.
        """
        user_info_url = "https://login.yandex.ru/info"
        params = {
            'format': 'json'
        }
        headers = {
            'Authorization': f"OAuth {access_token}"
        }

        response = requests.get(user_info_url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(f"Ошибка при получении информации о пользователе: {response.status_code} - {response.text}")
            raise Exception(_("Не удалось получить информацию о пользователе"))

        return response.json()

    def process_user_data(self, user_data):
        """
        Преобразует данные пользователя от Яндекса в стандартный формат.
        """
        # Разбиваем имя на составляющие
        name = user_data.get('real_name', '')
        name_parts = name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        return {
            'provider': self.provider_name,
            'provider_user_id': user_data.get('id'),
            'email': user_data.get('default_email'),
            'name': name,
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': f"https://avatars.yandex.net/get-yapic/{user_data.get('default_avatar_id')}/islands-200" if user_data.get(
                'default_avatar_id') else None,
            'raw_data': user_data
        }


class GitHubOAuthAdapter(BaseOAuthAdapter):
    """
    Адаптер для интеграции с GitHub OAuth.
    """
    provider_name = 'github'

    def __init__(self):
        self.client_id = getattr(settings, 'GITHUB_OAUTH_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'GITHUB_OAUTH_CLIENT_SECRET', None)

        if not self.client_id or not self.client_secret:
            logger.warning("GITHUB_OAUTH_CLIENT_ID или GITHUB_OAUTH_CLIENT_SECRET не настроены")

    def get_auth_url(self, redirect_uri, state=None):
        """
        Возвращает URL для авторизации через GitHub.
        """
        base_url = "https://github.com/login/oauth/authorize"
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'read:user user:email',
        }

        if state:
            params['state'] = state

        # Формируем URL с параметрами
        auth_url = f"{base_url}?"
        auth_url += "&".join([f"{key}={value}" for key, value in params.items()])

        return auth_url

    def exchange_code_for_token(self, code, redirect_uri):
        """
        Обменивает код авторизации на токен доступа.
        """
        token_url = "https://github.com/login/oauth/access_token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }
        headers = {
            'Accept': 'application/json'
        }

        response = requests.post(token_url, data=data, headers=headers)

        if response.status_code != 200:
            logger.error(f"Ошибка при обмене кода на токен: {response.status_code} - {response.text}")
            raise Exception(_("Не удалось обменять код авторизации на токен доступа"))

        return response.json()

    def get_user_info(self, access_token):
        """
        Получает информацию о пользователе от GitHub.
        """
        # Получаем базовую информацию о пользователе
        user_info_url = "https://api.github.com/user"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.get(user_info_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Ошибка при получении информации о пользователе: {response.status_code} - {response.text}")
            raise Exception(_("Не удалось получить информацию о пользователе"))

        user_data = response.json()

        # Получаем email пользователя (может быть приватным)
        emails_url = "https://api.github.com/user/emails"
        email_response = requests.get(emails_url, headers=headers)

        if email_response.status_code == 200:
            emails = email_response.json()
            # Ищем основной и проверенный email
            primary_email = next((email['email'] for email in emails if email['primary'] and email['verified']), None)
            if primary_email:
                user_data['email'] = primary_email

        return user_data

    def process_user_data(self, user_data):
        """
        Преобразует данные пользователя от GitHub в стандартный формат.
        """
        # Разбиваем имя на составляющие, если оно указано
        name = user_data.get('name', '')
        name_parts = name.split() if name else []
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        return {
            'provider': self.provider_name,
            'provider_user_id': str(user_data.get('id')),
            'email': user_data.get('email'),
            'name': name,
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': user_data.get('avatar_url'),
            'raw_data': user_data
        }