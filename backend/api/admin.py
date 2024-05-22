from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (CustomUser, Fav, Ingredient, Recipe, ShoppingList,
                     Subscription, Tag)


class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('first_name', 'last_name', 'email')


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorite_count')
    list_filter = ('name', 'author', 'tags')

    def get_favorite_count(self, obj):
        return obj.favorite_set.count()

    get_favorite_count.short_description = 'Число избранного'


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Fav)
admin.site.register(ShoppingList)
admin.site.register(Subscription)
