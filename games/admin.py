from django.contrib import admin

from .models import Game, GameParticipant


admin.site.register(Game)
admin.site.register(GameParticipant)
