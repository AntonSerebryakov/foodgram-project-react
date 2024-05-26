from django.contrib import admin

from recieps.models import (FavoriteRecipes, Ingredient, Recipe, ShoppingList,
                            Tag)
from users.models import Subscription


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorites_count')
    list_filter = ('name', 'author', 'tags')

    def get_favorites_count(self, obj):
        return FavoriteRecipes.objects.filter(recipe=obj).count()
    
    get_favorites_count.short_description = 'Число избранного'


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(FavoriteRecipes)
admin.site.register(ShoppingList)
admin.site.register(Subscription)
