from django.contrib import admin

from .models import Viaje


@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
    list_display = ("ruta", "bus", "fecha_hora_salida", "estado")
    search_fields = ("ruta__nombre", "bus__numero_interno", "bus__patente")
    list_filter = ("estado", "ruta", "bus")
    date_hierarchy = "fecha_hora_salida"
