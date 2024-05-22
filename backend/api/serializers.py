from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from .models import (Fav, Ingredient, Recipe, RecipeIngredient, ShoppingList,
                     Subscription, Tag)

User = get_user_model()


class UserInfoSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.subscriber.filter(author=obj).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=150,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(max_length=254, required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(
        max_length=150,
        required=True,
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, required=True)
    measurement_unit = serializers.CharField(max_length=10, required=True)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(source='ingredient.name')
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set',
                                             many=True,
                                             read_only=True)
    image = Base64ImageField(max_length=None, use_url=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'author',
                  'ingredients',
                  'image',
                  'tags',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'text',
                  'cooking_time',)
        read_only_fields = ('id', 'author',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_user = self.context['request'].user

    def get_is_favorited(self, obj):
        return (self.request_user.is_authenticated and
                Fav.objects.filter(user=self.request_user).exists())

    def get_is_in_shopping_cart(self, obj):
        return (self.request_user.is_authenticated and
                ShoppingList.objects.filter(user=self.request_user,
                                            recipe=obj).exists())


class IngredientCreateRecipeSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(min_value=1)
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)
    image = Base64ImageField(allow_empty_file=False, allow_null=False)
    ingredients = IngredientCreateRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'name',
            'ingredients',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ('id', 'author')

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Ингредиенты не выбраны')

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты в '
                                              'рецепте повторяются.')

        if not Ingredient.objects.filter(id__in=ingredient_ids).exists():
            raise serializers.ValidationError('Ингредиент не существует.')
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError('Теги отсутствуют')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги повторяется')
        if not Tag.objects.filter(name__in=tags).exists():
            raise serializers.ValidationError('Один из тегов не существует.')
        image = data.get('image')
        if not image:
            raise serializers.ValidationError('Изображение не предоставлено.')

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        with transaction.atomic():
            author = self.context['request'].user
            recipe = Recipe.objects.create(author=author, **validated_data)
            recipe.tags.set(tags)
            self.create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        with transaction.atomic():
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ingredients(instance, ingredients_data)
            instance.tags.set(tags)

        return super().update(instance, validated_data)

    def create_ingredients(self, recipe, ingredients):
        create_ingredients = []
        for ingredient in ingredients:
            ingredient_obj = RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            )
            create_ingredients.append(ingredient_obj)
        RecipeIngredient.objects.bulk_create(create_ingredients)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context={
            'request': self.context['request']
        }).data


class MiniRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        read_only=True
    )

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора!',
            ),
        ]

    def validate(self, data):
        author = data.get('author')
        user = self.context.get('request').user

        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя.')

        return data

    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        return UserSubscribesSerializer(
            instance.author, context={'request': self.context.get('request')}
        ).data


class UserSubscribesSerializer(UserInfoSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return MiniRecipeSerializer(
            recipes, context={'request': request}, many=True
        ).data

    def get_recipes_count(self, obj):

        return obj.recipes.count()
