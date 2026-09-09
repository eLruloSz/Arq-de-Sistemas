from django.db import transaction
from django.db.models.deletion import ProtectedError

from .models import Ruta, RutaParada


class RouteInUseError(Exception):
    """No se pueden reemplazar paradas referenciadas por datos existentes."""


def replace_route_stops(*, route, stops):
    """Reemplaza una configuración validada conservando integridad histórica."""
    with transaction.atomic():
        locked_route = Ruta.objects.select_for_update().get(pk=route.pk)
        if locked_route.viajes.exists() or locked_route.tarifas.exists():
            raise RouteInUseError(
                "La ruta tiene viajes o tarifas; sus paradas no se reemplazan."
            )
        try:
            locked_route.paradas_ruta.all().delete()
        except ProtectedError as exc:
            raise RouteInUseError(
                "Las paradas están referenciadas por datos históricos."
            ) from exc
        RutaParada.objects.bulk_create([
            RutaParada(
                ruta=locked_route,
                parada=item["stop_id"],
                orden=item["order"],
                minutos_desde_origen=item["minutes_from_origin"],
            )
            for item in stops
        ])
