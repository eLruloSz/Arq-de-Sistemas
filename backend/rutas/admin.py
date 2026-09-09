from django.contrib import admin

from .models import Parada, Ruta, RutaParada, Tarifa


class RutaParadaInline(admin.TabularInline):
    model = RutaParada
    extra = 0
    ordering = ("orden",)


@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "activo")
    search_fields = ("nombre", "ciudad", "direccion")
    list_filter = ("activo", "ciudad")


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activa",)
    inlines = (RutaParadaInline,)


@admin.register(RutaParada)
class RutaParadaAdmin(admin.ModelAdmin):
    list_display = (
        "ruta",
        "orden",
        "parada",
        "minutos_desde_origen",
    )
    search_fields = ("ruta__nombre", "parada__nombre", "parada__ciudad")
    list_filter = ("ruta",)
    ordering = ("ruta", "orden")


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ("ruta", "origen", "destino", "precio", "activa")
    search_fields = (
        "ruta__nombre",
        "origen__parada__nombre",
        "destino__parada__nombre",
    )
    list_filter = ("activa", "ruta")
