from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from accounts.models import Profile, Role, RoleAssignment

User = get_user_model()


class UserForm(forms.ModelForm):
    """
    Форма для создания и редактирования пользователя.
    """

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_active', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # Поле для возможности создания пользователя с паролем
    password = forms.CharField(
        label=_('Пароль'),
        required=False,  # Не обязательно при редактировании
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_('Оставьте пустым, если не хотите менять пароль существующего пользователя.')
    )

    confirm_password = forms.CharField(
        label=_('Подтверждение пароля'),
        required=False,  # Не обязательно при редактировании
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        # Если редактируем существующего пользователя
        self.instance_user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        # Если создаем нового пользователя, пароль обязателен
        if not self.instance_user:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

    def clean_username(self):
        """
        Проверяет, что имя пользователя уникально.
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(_('Пользователь с таким именем уже существует.'))
        return username

    def clean_email(self):
        """
        Проверяет, что email уникален.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def clean(self):
        """
        Проверяет, что пароли совпадают.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and password != confirm_password:
            self.add_error('confirm_password', _('Пароли не совпадают.'))

        return cleaned_data

    def save(self, commit=True):
        """
        Сохраняет пользователя с зашифрованным паролем, если он указан.
        """
        user = super().save(commit=False)

        # Устанавливаем пароль, если он указан
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user


class UserProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя.
    """

    class Meta:
        model = Profile
        fields = ('position', 'department', 'bio', 'date_of_birth', 'language', 'timezone')
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
        }

    # Добавляем поле для загрузки аватара
    avatar = forms.ImageField(
        label=_('Аватар'),
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавляем языки
        LANGUAGE_CHOICES = [
            ('ru', _('Русский')),
            ('en', _('Английский')),
            ('de', _('Немецкий')),
            ('fr', _('Французский')),
            ('es', _('Испанский')),
        ]
        self.fields['language'].choices = LANGUAGE_CHOICES

        # Добавляем часовые пояса
        TIMEZONE_CHOICES = [
            ('Europe/Moscow', _('Москва (UTC+3)')),
            ('Europe/Kaliningrad', _('Калининград (UTC+2)')),
            ('Europe/Samara', _('Самара (UTC+4)')),
            ('Asia/Yekaterinburg', _('Екатеринбург (UTC+5)')),
            ('Asia/Omsk', _('Омск (UTC+6)')),
            ('Asia/Krasnoyarsk', _('Красноярск (UTC+7)')),
            ('Asia/Irkutsk', _('Иркутск (UTC+8)')),
            ('Asia/Yakutsk', _('Якутск (UTC+9)')),
            ('Asia/Vladivostok', _('Владивосток (UTC+10)')),
            ('Asia/Magadan', _('Магадан (UTC+11)')),
            ('Asia/Kamchatka', _('Камчатка (UTC+12)')),
            ('Europe/London', _('Лондон (UTC+0)')),
            ('America/New_York', _('Нью-Йорк (UTC-5)')),
            ('America/Los_Angeles', _('Лос-Анджелес (UTC-8)')),
        ]
        self.fields['timezone'].choices = TIMEZONE_CHOICES

    def save(self, commit=True):
        """
        Сохраняет профиль пользователя и аватар, если он загружен.
        """
        profile = super().save(commit=False)

        # Сохраняем аватар, если он загружен
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            profile.avatar = avatar

        if commit:
            profile.save()

        return profile


class UserRoleForm(forms.Form):
    """
    Форма для назначения роли пользователю.
    """
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        label=_('Роль'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    expires_at = forms.DateTimeField(
        label=_('Срок действия'),
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        help_text=_('Оставьте пустым, если роль назначается бессрочно.')
    )

    def __init__(self, user=None, *args, **kwargs):
        """
        Инициализация формы с пользователем, которому назначается роль.
        """
        self.user = user
        super().__init__(*args, **kwargs)

        # Если пользователь указан, исключаем роли, которые у него уже есть
        if user:
            assigned_role_ids = RoleAssignment.objects.filter(user=user).values_list('role_id', flat=True)
            self.fields['role'].queryset = Role.objects.exclude(id__in=assigned_role_ids)

    def clean(self):
        """
        Проверяет, что выбранная роль не назначена пользователю ранее.
        """
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if self.user and role:
            if RoleAssignment.objects.filter(user=self.user, role=role).exists():
                self.add_error('role', _('Эта роль уже назначена пользователю.'))

        return cleaned_data

    def save(self, assigned_by=None):
        """
        Создает связь между пользователем и ролью.

        Args:
            assigned_by: Пользователь, который назначает роль

        Returns:
            RoleAssignment: Объект назначения роли
        """
        if not self.user:
            raise ValueError(_("Пользователь не указан."))

        role = self.cleaned_data.get('role')
        expires_at = self.cleaned_data.get('expires_at')

        role_assignment = RoleAssignment.objects.create(
            user=self.user,
            role=role,
            assigned_by=assigned_by,
            expires_at=expires_at
        )

        return role_assignment