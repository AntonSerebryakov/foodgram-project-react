from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from .constants import (MAX_INGREDIENT_LENGTH, MAX_MEASURMENT_UNIT_LENGTH,
                        MAX_RECIPE_NAME_LENGTH, MAX_TAG_NAME_LENGTH,
                        MAX_TAG_SLUG_LENGTH)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_INGREDIENT_LENGTH, blank=False)
    measurement_unit = models.CharField(max_length=MAX_MEASURMENT_UNIT_LENGTH,
                                        blank=False)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_measurement'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=MAX_TAG_NAME_LENGTH, unique=True)
    color = ColorField(default='#FFFFFF', verbose_name='Цвет')
    slug = models.SlugField(max_length=MAX_TAG_SLUG_LENGTH,
                            unique=True,
                            verbose_name='SLUG')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):

    name = models.CharField(max_length=MAX_RECIPE_NAME_LENGTH)
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)])
    text = models.TextField()
    image = models.ImageField(upload_to='static/recipes/')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes')
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f'{self.ingredient.name} - {self.amount}'


class SelectedRecipes(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('user', 'recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user',),
                name='unique_user_recipe',)
        ]
        abstract = True


class FavoriteRecipes(SelectedRecipes):
    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранные'
        verbose_name_plural = 'Избранные'


class ShoppingList(SelectedRecipes):
    class Meta:
        default_related_name = 'shoppinglist'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'


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
