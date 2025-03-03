from accounts.forms.auth_forms import (
    LoginForm, RegistrationForm, PasswordResetForm,
    PasswordResetConfirmForm, PasswordChangeForm
)

from accounts.forms.user_forms import (
    UserForm, UserProfileForm, UserRoleForm
)

__all__ = [
    # Формы аутентификации
    'LoginForm',
    'RegistrationForm',
    'PasswordResetForm',
    'PasswordResetConfirmForm',
    'PasswordChangeForm',

    # Формы пользователей
    'UserForm',
    'UserProfileForm',
    'UserRoleForm',
]