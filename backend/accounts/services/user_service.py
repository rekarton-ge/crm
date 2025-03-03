from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import UserActivity

User = get_user_model()


class UserService:
    """
    Сервисный класс для управления пользователями (создание, обновление, деактивация).
    """

    @staticmethod
    def create_user(username, email, password, first_name='', last_name='',
                    phone_number=None, is_active=True, is_staff=False,
                    created_by=None, roles=None):
        """
        Создает нового пользователя с указанными параметрами.
        """
        with transaction.atomic():
            # Создаем пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                is_active=is_active,
                is_staff=is_staff
            )

            # Назначаем роли, если указаны
            if roles:
                from accounts.services.permission_service import PermissionService
                for role in roles:
                    PermissionService.assign_role_to_user(user, role, assigned_by=created_by)

            # Логируем действие, если указан создатель
            if created_by:
                UserActivity.log_activity(
                    user=created_by,
                    activity_type='create',
                    description=f'Создание пользователя {username}',
                    object_type='accounts.user',
                    object_id=str(user.id)
                )

            return user

    @staticmethod
    def update_user(user, updated_by=None, **kwargs):
        """
        Обновляет данные пользователя.
        """
        with transaction.atomic():
            # Обновляем поля пользователя
            for key, value in kwargs.items():
                if hasattr(user, key) and key not in ('password',):
                    setattr(user, key, value)

            # Если указан новый пароль
            if 'password' in kwargs and kwargs['password']:
                user.set_password(kwargs['password'])

            user.save()

            # Логируем действие, если указан обновляющий
            if updated_by:
                UserActivity.log_activity(
                    user=updated_by,
                    activity_type='update',
                    description=f'Обновление пользователя {user.username}',
                    object_type='accounts.user',
                    object_id=str(user.id)
                )

            return user

    @staticmethod
    def update_profile(user, updated_by=None, **kwargs):
        """
        Обновляет профиль пользователя.
        """
        with transaction.atomic():
            profile = user.profile

            # Обновляем поля профиля
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            profile.save()

            # Логируем действие, если указан обновляющий
            if updated_by:
                UserActivity.log_activity(
                    user=updated_by,
                    activity_type='update',
                    description=f'Обновление профиля пользователя {user.username}',
                    object_type='accounts.profile',
                    object_id=str(profile.id)
                )

            return profile

    @staticmethod
    def deactivate_user(user, deactivated_by=None):
        """
        Деактивирует пользователя (мягкое удаление).
        """
        with transaction.atomic():
            user.is_active = False
            user.save(update_fields=['is_active'])

            # Завершаем все активные сессии пользователя
            from accounts.services.auth_service import AuthService
            AuthService.end_all_sessions(user)

            # Логируем действие, если указан деактивирующий
            if deactivated_by:
                UserActivity.log_activity(
                    user=deactivated_by,
                    activity_type='update',
                    description=f'Деактивация пользователя {user.username}',
                    object_type='accounts.user',
                    object_id=str(user.id)
                )

            return user

    @staticmethod
    def activate_user(user, activated_by=None):
        """
        Активирует пользователя.
        """
        with transaction.atomic():
            user.is_active = True
            user.save(update_fields=['is_active'])

            # Логируем действие, если указан активирующий
            if activated_by:
                UserActivity.log_activity(
                    user=activated_by,
                    activity_type='update',
                    description=f'Активация пользователя {user.username}',
                    object_type='accounts.user',
                    object_id=str(user.id)
                )

            return user

    @staticmethod
    def change_password(user, new_password, changed_by=None):
        """
        Изменяет пароль пользователя.
        """
        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=['password'])

            # Логируем действие
            if changed_by:
                actor = changed_by
            else:
                actor = user

            UserActivity.log_activity(
                user=actor,
                activity_type='update',
                description=(f'Изменение пароля пользователя {user.username}'
                             if actor != user else 'Изменение своего пароля'),
                object_type='accounts.user',
                object_id=str(user.id)
            )

            return user

    @staticmethod
    def get_user_activity(user, activity_type=None, start_date=None, end_date=None,
                          page=1, page_size=20):
        """
        Получает журнал активности пользователя с фильтрацией.
        """
        activities = UserActivity.objects.filter(user=user)

        # Применяем фильтры, если указаны
        if activity_type:
            activities = activities.filter(activity_type=activity_type)

        if start_date:
            activities = activities.filter(timestamp__gte=start_date)

        if end_date:
            activities = activities.filter(timestamp__lte=end_date)

        # Сортируем по убыванию времени
        activities = activities.order_by('-timestamp')

        # Пагинация
        from django.core.paginator import Paginator
        paginator = Paginator(activities, page_size)
        page_obj = paginator.get_page(page)

        return {
            'items': page_obj.object_list,
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': page_obj.number
        }