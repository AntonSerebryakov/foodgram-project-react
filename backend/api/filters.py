from django_filters import rest_framework
from recieps.models import Ingredient, Recipe, Tag


class IngredientSearch(rest_framework.FilterSet):
    name = rest_framework.CharFilter(
        field_name='name',
        lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(rest_framework.FilterSet):

    is_favorited = rest_framework.BooleanFilter(
        method='is_recipe_in_favorites_filter')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='is_recipe_in_shoppingcart_filter')
    tags = rest_framework.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')

    def is_recipe_in_favorites_filter(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user_id=self.request.user.id)
        return queryset

    def is_recipe_in_shoppingcart_filter(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(
                shoppinglist__user_id=self.request.user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')
