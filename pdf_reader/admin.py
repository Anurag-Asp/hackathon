from django.contrib import admin
from .models import PDFDocument,ChatMessage, CustomUser
from django.contrib.auth.admin import UserAdmin


admin.site.register(CustomUser, UserAdmin)

# Register your models here.
admin.site.register(PDFDocument)
admin.site.register(ChatMessage)