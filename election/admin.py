from django.contrib import admin

from .models import Election, Vote, Token

admin.site.register(Vote)
admin.site.register(Token)


class ElectionAdmin(admin.ModelAdmin):
    list_display = (
            'title', 
            'candidates',
            'on_invitation_only',
            'num_grades',
            'start_at',
            'finish_at',
            'select_language',
            'restrict_results'
    )

admin.site.register(Election, ElectionAdmin)
