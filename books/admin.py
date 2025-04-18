from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Book)
admin.site.register(BookComment)
admin.site.register(FriendRequest)
admin.site.register(Message)