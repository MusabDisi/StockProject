from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Stock)
admin.site.register(UserProfile)
admin.site.register(Sector)
admin.site.register(Notification)
admin.site.register(ReadyNotification)
