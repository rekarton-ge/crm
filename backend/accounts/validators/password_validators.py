import re
import string
from difflib import SequenceMatcher
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class MinimumLengthValidator:
    """
    Валидатор, который проверяет, что пароль имеет минимальную длину.
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        """
        Проверяет, что пароль не короче минимальной длины.
        """
        if len(password) < self.min_length:
            raise ValidationError(
                _("Этот пароль слишком короткий. Он должен содержать минимум %(min_length)d символов."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        """
        Возвращает текст подсказки для пользователя.
        """
        return _(
            "Ваш пароль должен содержать минимум %(min_length)d символов."
        ) % {'min_length': self.min_length}


class CommonPasswordValidator:
    """
    Валидатор, который проверяет, не входит ли пароль в список распространенных паролей.
    """

    def __init__(self, common_passwords=None):
        # Список наиболее распространенных паролей
        self.common_passwords = common_passwords or [
            "123456", "password", "123456789", "12345678", "12345", "1234567", "1234567890",
            "qwerty", "abc123", "111111", "123123", "admin", "welcome", "monkey", "login",
            "qwerty123", "123qwe", "1q2w3e4r", "passw0rd", "qwertyuiop", "654321", "555555",
            "7777777", "1234", "12345", "123456", "1234567", "12345678", "123456789",
            "password", "qwerty", "abc123", "football", "1234567890", "123123", "monkey",
            "letmein", "1111", "111111", "dragon", "sunshine", "master", "666666", "qwertyuiop",
            "123321", "mustang", "121212", "000000", "trustno1", "password1", "welcome",
            "admin", "!@#$%^&*", "shadow", "michael", "princess", "baseball", "superman",
            "hannah", "ashley", "lovely", "angel", "donald", "jennifer", "summer", "iloveyou"
        ]

    def validate(self, password, user=None):
        """
        Проверяет, не входит ли пароль в список распространенных паролей.
        """
        if password.lower() in self.common_passwords:
            raise ValidationError(
                _("Этот пароль слишком распространен и не является безопасным."),
                code='password_too_common',
            )

    def get_help_text(self):
        """
        Возвращает текст подсказки для пользователя.
        """
        return _(
            "Ваш пароль не должен входить в список распространенных паролей."
        )


class NumericPasswordValidator:
    """
    Валидатор, который требует наличия цифр в пароле.
    """

    def __init__(self, min_digits=1):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        """
        Проверяет, что пароль содержит как минимум указанное количество цифр.
        """
        digit_count = sum(1 for char in password if char in string.digits)
        if digit_count < self.min_digits:
            raise ValidationError(
                _(
                    "Пароль должен содержать как минимум %(min_digits)d цифр."
                ),
                code='password_too_few_digits',
                params={'min_digits': self.min_digits},
            )

    def get_help_text(self):
        """
        Возвращает текст подсказки для пользователя.
        """
        return _(
            "Ваш пароль должен содержать как минимум %(min_digits)d цифр."
        ) % {'min_digits': self.min_digits}


class UppercasePasswordValidator:
    """
    Валидатор, который требует наличия заглавных букв в пароле.
    """

    def __init__(self, min_uppercase=1):
        self.min_uppercase = min_uppercase

    def validate(self, password, user=None):
        """
        Проверяет, что пароль содержит как минимум указанное количество заглавных букв.
        """
        uppercase_count = sum(1 for char in password if char.isupper())
        if uppercase_count < self.min_uppercase:
            raise ValidationError(
                _(
                    "Пароль должен содержать как минимум %(min_uppercase)d заглавных букв."
                ),
                code='password_too_few_uppercase',
                params={'min_uppercase': self.min_uppercase},
            )

    def get_help_text(self):
        """
        Возвращает текст подсказки для пользователя.
        """
        return _(
            "Ваш пароль должен содержать как минимум %(min_uppercase)d заглавных букв."
        ) % {'min_uppercase': self.min_uppercase}


class SpecialCharacterPasswordValidator:
    """
    Валидатор, который требует наличия специальных символов в пароле.
    """

    def __init__(self, min_special=1, special_chars=None):
        self.min_special = min_special
        self.special_chars = special_chars or ''.join([
            c for c in string.punctuation
        ])

    def validate(self, password, user=None):
        """
        Проверяет, что пароль содержит как минимум указанное количество специальных символов.
        """
        special_count = sum(1 for char in password if char in self.special_chars)
        if special_count < self.min_special:
            raise ValidationError(
                _(
                    "Пароль должен содержать как минимум %(min_special)d специальных символов (например, %(chars)s)."
                ),
                code='password_too_few_special',
                params={
                    'min_special': self.min_special,
                    'chars': self.special_chars[:5] + "..."
                },
            )

    def get_help_text(self):
        """
        Возвращает текст подсказки для пользователя.
        """
        return _(
            "Ваш пароль должен содержать как минимум %(min_special)d специальных символов (например, %(chars)s)."
        ) % {
            'min_special': self.min_special,
            'chars': self.special_chars[:5] + "..."
        }


class UserAttributePasswordValidator:
    """
    Валидатор, который проверяет, что пароль не содержит личной информации пользователя.
    """

    def __init__(self, user_attributes=None, max_similarity=0.7):
        self.user_attributes = user_attributes or ['username', 'email', 'first_name', 'last_name']
        self.max_similarity = max_similarity

    def validate(self, password, user=None):
        """
        Проверяет, что пароль не содержит личной информации пользователя.
        """
        if user:
            for attribute_name in self.user_attributes:
                # Получаем значение атрибута пользователя
                attribute_value = getattr(user, attribute_name, None)
                if attribute_value:
                    # Если атрибут - это email, используем только часть до @
                    if attribute_name == 'email' and '@' in attribute_value:
                        attribute_value = attribute_value.split('@')[0]

                    # Проверяем схожесть
                    if self._is_too_similar(password, attribute_value):
                        raise ValidationError(
                            _(
                                "Пароль слишком похож на ваш %(attribute_name)s."
                            ),
                            code='password_too_similar',
                            params={'attribute_name': attribute_name},
                        )

    def _is_too_similar(self, password, value):
        """
        Проверяет, не слишком ли похожи пароль и значение атрибута.
        """
        # Если значение содержится в пароле или наоборот
        if value.lower() in password.lower() or password.lower() in value.lower():
            return True

        # Проверяем схожесть с помощью SequenceMatcher
        similarity = SequenceMatcher(None, password.lower(), value.lower()).ratio()
        return similarity >= self.max_similarity

    def get_help_text(self):
        """
        Возвращает текст подсказки для пользователя.
        """
        return _(
            "Ваш пароль не должен быть похож на вашу личную информацию."
        )


# Пример настройки для settings.py
DEFAULT_PASSWORD_VALIDATORS = [
    {
        'NAME': 'accounts.validators.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'accounts.validators.CommonPasswordValidator',
    },
    {
        'NAME': 'accounts.validators.NumericPasswordValidator',
    },
    {
        'NAME': 'accounts.validators.UppercasePasswordValidator',
    },
    {
        'NAME': 'accounts.validators.SpecialCharacterPasswordValidator',
    },
    {
        'NAME': 'accounts.validators.UserAttributePasswordValidator',
    },
]