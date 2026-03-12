from django.contrib import admin

from api.models import Character, Run, UserCharacterSelected, User

admin.site.register(Character)
admin.site.register(Run)
admin.site.register(User)
admin.site.register(UserCharacterSelected)
