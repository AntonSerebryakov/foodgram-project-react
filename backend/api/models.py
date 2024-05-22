from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.forms import ValidationError


class CustomUser(AbstractUser):
    email = models.EmailField('email address', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'], name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ['name']


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=50,
                             unique=True,
                             verbose_name='Hex код цвета')
    slug = models.SlugField(max_length=50,
                            unique=True,
                            verbose_name='SLUG')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipe(models.Model):

    name = models.CharField(max_length=100)
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)])
    text = models.TextField()
    image = models.ImageField(upload_to='static/recipes/')
    author = models.ForeignKey(CustomUser,
                               on_delete=models.CASCADE,
                               related_name='recipes')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.ingredient.name} - {self.amount}'


class Fav(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='favorites')
    user = models.ForeignKey(CustomUser,
                             on_delete=models.CASCADE,
                             related_name='favorites')

    class Meta:
        default_related_name = 'favorites'
        ordering = ['-id']
        verbose_name = 'Избранные'
        verbose_name_plural = 'Избранные'

        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_user_recipe',

            )
        ]


class ShoppingList(models.Model):

    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='shopping_reciep')
    user = models.ForeignKey(CustomUser,
                             on_delete=models.CASCADE,
                             related_name='shopping_user')

    class Meta:
        ordering = ('user', 'recipe',)
        default_related_name = 'in_shop_list'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_recipe_in_list',
            )
        ]


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name="Подписчик",
        related_name="subscriber",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        CustomUser,
        verbose_name="Автор рецепта",
        related_name="author",
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
                fields=('user', 'author'), name='unique_subscription'
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
