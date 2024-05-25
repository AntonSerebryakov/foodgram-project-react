from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import (MAX_EMAIL_LENGTH, MAX_FIRSTNAME_LENGTH,
                        MAX_LASTNAME_LENGTH, MAX_USERNAME_LENGTH)


class User(AbstractUser):
    email = models.EmailField('email address',
                              max_length=MAX_EMAIL_LENGTH,
                              unique=True)
    username = models.CharField(
        'first name',
        max_length=MAX_USERNAME_LENGTH,
        blank=False,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Имя содержит недопустимые символы.',
                code='invalid_username'
            )
        ],
    )
    first_name = models.CharField('first name',
                                  max_length=MAX_FIRSTNAME_LENGTH,
                                  blank=False)
    last_name = models.CharField('last name',
                                 max_length=MAX_LASTNAME_LENGTH,
                                 blank=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('first_name', 'last_name', 'username',)

    def __str__(self):
        return self.username
