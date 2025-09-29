from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.

@admin.register(User)
class UserAdmin(UserAdmin):
    """Define admin model for custom User model."""

    list_display = ('email', 'name', 'is_staff', )
    search_fields = ('email', 'name', 'is_staff', )
    ordering = ('id', )
    fieldsets = (
        (None, {
            "fields": (
                ('email', 'name', 'is_staff',)
            ),
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )

@admin.register(ThreadTemplate)
class SessionTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(Thread)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'title', )
    pass

@admin.register(Tick)
class TickAdmin(admin.ModelAdmin):
    pass
