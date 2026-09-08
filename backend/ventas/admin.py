from django.contrib import admin

from .models import DetalleReserva, Pago, Pasajero, Reserva


class DetalleReservaInline(admin.TabularInline):
    model = DetalleReserva
    extra = 0


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "usuario",
        "viaje",
        "origen",
        "destino",
        "estado",
        "total",
        "created_at",
    )
    search_fields = (
        "codigo",
        "usuario__username",
        "usuario__email",
        "viaje__ruta__nombre",
    )
    list_filter = ("estado", "viaje__ruta")
    date_hierarchy = "created_at"
    readonly_fields = ("codigo", "created_at")
    inlines = (DetalleReservaInline,)


@admin.register(Pasajero)
class PasajeroAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "apellido",
        "tipo_documento",
        "documento",
        "reserva",
    )
    search_fields = ("nombre", "apellido", "documento", "reserva__codigo")
    list_filter = ("tipo_documento",)


@admin.register(DetalleReserva)
class DetalleReservaAdmin(admin.ModelAdmin):
    list_display = ("reserva", "pasajero", "asiento", "precio_unitario")
    search_fields = (
        "reserva__codigo",
        "pasajero__nombre",
        "pasajero__apellido",
        "asiento__numero",
    )
    list_filter = ("reserva__viaje__ruta",)


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("reserva", "monto", "estado", "created_at", "paid_at")
    search_fields = ("reserva__codigo", "reserva__usuario__username")
    list_filter = ("estado",)
    date_hierarchy = "created_at"
