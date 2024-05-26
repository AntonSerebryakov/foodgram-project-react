from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.forms import ValidationError

from .constants import (MAX_EMAIL_LENGTH, MAX_FIRSTNAME_LENGTH,
                        MAX_LASTNAME_LENGTH, MAX_USERNAME_LENGTH)


class User(AbstractUser):
    email = models.EmailField('email address',
                              max_length=MAX_EMAIL_LENGTH,
                              unique=True)
    username = models.CharField(
        'username',
        max_length=MAX_USERNAME_LENGTH,
        blank=False,
        unique=True,
        validators=(UnicodeUsernameValidator(),),
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


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='subscriber',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='author',
        on_delete=models.CASCADE,
    )

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на себя')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='user_not_subscribe_self',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
