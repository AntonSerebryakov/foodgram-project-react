from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recieps.models import (FavoriteRecipes, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Subscription, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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
        return (request and request.user.is_authenticated
                and request.user.subscriber.filter(author=obj).exists())


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='ingredient.name')
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and FavoriteRecipes.objects.filter(
                    user=request.user,
                    recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')

        return (request and request.user.is_authenticated
                and ShoppingList.objects.filter(user=request.user,
                                                recipe=obj).exists())


class IngredientCreateRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    image = Base64ImageField(allow_empty_file=False, allow_null=False)
    ingredients = IngredientCreateRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'name',
            'ingredients',
            'image',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Ингредиенты не выбраны')
        ingredient_ids = [ingredient['ingredient'].id
                          for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты в '
                                              'рецепте повторяются.')

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError('Теги отсутствуют')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги повторя.тся')
        image = data.get('image')
        if not image:
            raise serializers.ValidationError('Изображение не предоставлено.')

        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.clear()
        self.create_ingredients(instance, ingredients_data)
        instance.tags.set(tags)
        return super().update(instance, validated_data)

    def create_ingredients(self, recipe, ingredients):
        create_ingredients = []
        for ingredient_data in ingredients:
            ingredient = ingredient_data.pop('ingredient')
            create_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
            )
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


class FavRecipeCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = FavoriteRecipes
        fields = ('recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipes.objects.all(),
                fields=('recipe', 'user'),
                message='Вы уже подписаны на этого автора!',
            ),
        ]

    def to_representation(self, instance):
        return MiniRecipeSerializer(
            instance.recipe).data


class ShoppingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingList
        fields = ('recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже в корзине!',
            ),
        ]

    def to_representation(self, instance):
        return MiniRecipeSerializer(
            instance.recipe).data
