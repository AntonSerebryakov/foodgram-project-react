from django_filters import rest_framework,filters

from .models import Ingredient, Tag, Recipe


class IngredientSearch(rest_framework.FilterSet):
    name = rest_framework.CharFilter(
        field_name='name',
        lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)

class RecipeFilter(rest_framework.FilterSet):
    
    is_favorited = filters.NumberFilter(
        method='is_recipe_in_favorites_filter')
    is_in_shopping_cart = filters.NumberFilter(
        method='is_recipe_in_shoppingcart_filter')
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')

    def is_recipe_in_favorites_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(favorites__user_id=user.id)
        return queryset

    def is_recipe_in_shoppingcart_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(shopping_reciep__user_id=user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')