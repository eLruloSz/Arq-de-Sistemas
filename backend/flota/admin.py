from django.contrib import admin

from .models import Asiento, Bus


class AsientoInline(admin.TabularInline):
    model = Asiento
    extra = 0


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ("numero_interno", "patente", "marca", "modelo", "activo")
    search_fields = ("numero_interno", "patente", "marca", "modelo")
    list_filter = ("activo", "marca")
    inlines = (AsientoInline,)


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ("numero", "bus", "fila", "columna", "activo")
    search_fields = ("numero", "bus__numero_interno", "bus__patente")
    list_filter = ("activo", "bus")
