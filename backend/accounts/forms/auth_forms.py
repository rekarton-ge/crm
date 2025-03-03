from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class LoginForm(forms.Form):
    """
    Форма для входа пользователя в систему.
    """
    username = forms.CharField(
        label=_('Имя пользователя или Email'),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите имя пользователя или email')})
    )
    password = forms.CharField(
        label=_('Пароль'),
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Введите пароль')})
    )
    remember_me = forms.BooleanField(
        label=_('Запомнить меня'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        """
        Проверяет корректность учетных данных пользователя.
        """
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Проверяем, может ли пользователь войти
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError(_('Неверное имя пользователя или пароль.'), code='invalid_login')
            elif not user.is_active:
                raise forms.ValidationError(_('Этот аккаунт деактивирован.'), code='inactive')

            # Если пользователь прошел проверку, сохраняем его в форме
            self.user = user

        return cleaned_data


class RegistrationForm(forms.ModelForm):
    """
    Форма для регистрации нового пользователя.
    """
    password1 = forms.CharField(
        label=_('Пароль'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Введите пароль')}),
        help_text=_('Пароль должен содержать минимум 8 символов, включая буквы и цифры.')
    )
    password2 = forms.CharField(
        label=_('Подтверждение пароля'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Повторите пароль')}),
        help_text=_('Введите тот же пароль еще раз для проверки.')
    )
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Введите email')}),
        help_text=_('Введите действующий email адрес. На него будет отправлено письмо для активации.')
    )
    agree_terms = forms.BooleanField(
        label=_('Я согласен с условиями использования'),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите имя пользователя')}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите имя')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите фамилию')}),
        }
        help_texts = {
            'username': _('Обязательное поле. До 150 символов. Только буквы, цифры и символы @/./+/-/_.'),
        }

    def clean_username(self):
        """
        Проверяет, что имя пользователя уникально.
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('Пользователь с таким именем уже существует.'))
        return username

    def clean_email(self):
        """
        Проверяет, что email уникален.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def clean_password2(self):
        """
        Проверяет, что оба пароля совпадают.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Пароли не совпадают.'))
        return password2

    def save(self, commit=True):
        """
        Сохраняет пользователя с зашифрованным паролем.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class PasswordResetForm(DjangoPasswordResetForm):
    """
    Форма для запроса сброса пароля.
    Расширяет стандартную форму Django для кастомизации.
    """
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Введите ваш email')})
    )

    def clean_email(self):
        """
        Проверяет, что email существует в системе.
        """
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            # По соображениям безопасности не сообщаем пользователю,
            # что такого email не существует
            pass
        return email


class PasswordResetConfirmForm(SetPasswordForm):
    """
    Форма для ввода нового пароля при сбросе.
    Расширяет стандартную форму Django для кастомизации.
    """
    new_password1 = forms.CharField(
        label=_('Новый пароль'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Введите новый пароль')}),
        help_text=_('Пароль должен содержать минимум 8 символов, включая буквы и цифры.')
    )
    new_password2 = forms.CharField(
        label=_('Подтверждение нового пароля'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Повторите новый пароль')}),
    )


class PasswordChangeForm(forms.Form):
    """
    Форма для изменения пароля пользователя.
    """
    old_password = forms.CharField(
        label=_('Текущий пароль'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Введите текущий пароль')})
    )
    new_password1 = forms.CharField(
        label=_('Новый пароль'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Введите новый пароль')}),
        help_text=_('Пароль должен содержать минимум 8 символов, включая буквы и цифры.')
    )
    new_password2 = forms.CharField(
        label=_('Подтверждение нового пароля'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Повторите новый пароль')})
    )

    def __init__(self, user, *args, **kwargs):
        """
        Инициализация формы с пользователем.
        """
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """
        Проверяет, что текущий пароль введен правильно.
        """
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(_('Неверный текущий пароль.'))
        return old_password

    def clean_new_password2(self):
        """
        Проверяет, что оба новых пароля совпадают.
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Новые пароли не совпадают.'))
        return password2

    def save(self, commit=True):
        """
        Сохраняет новый пароль для пользователя.
        """
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user