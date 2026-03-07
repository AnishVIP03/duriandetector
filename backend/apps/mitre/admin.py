from django.contrib import admin
from .models import MitreTactic, MitreTechnique


@admin.register(MitreTactic)
class MitreTacticAdmin(admin.ModelAdmin):
    list_display = ['tactic_id', 'name']
    search_fields = ['tactic_id', 'name']


@admin.register(MitreTechnique)
class MitreTechniqueAdmin(admin.ModelAdmin):
    list_display = ['technique_id', 'name', 'tactic']
    list_filter = ['tactic']
    search_fields = ['technique_id', 'name']
