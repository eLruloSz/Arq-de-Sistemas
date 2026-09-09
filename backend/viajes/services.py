"""Consultas de viajes que reutilizan las reglas centrales de ventas."""
from datetime import UTC, datetime, time, timedelta

from django.utils import timezone

from rutas.models import Tarifa
from ventas.exceptions import InvalidSegmentError
from ventas.services import get_available_seats

from .models import Viaje


def resolve_segment(*, viaje, origin, destination):
    stops = {
        stop.parada_id: stop
        for stop in viaje.ruta.paradas_ruta.select_related("parada").filter(
            parada_id__in=(origin.pk, destination.pk),
        )
    }
    try:
        return stops[origin.pk], stops[destination.pk]
    except KeyError as exc:
        raise InvalidSegmentError(
            "Ambas paradas deben pertenecer a la ruta del viaje."
        ) from exc


def search_trips(*, origin, destination, date):
    fares = list(Tarifa.objects.filter(
        activa=True,
        ruta__activa=True,
        origen__parada=origin,
        destino__parada=destination,
    ).select_related("ruta", "origen", "destino"))
    if not fares:
        return []

    fares_by_route = {fare.ruta_id: fare for fare in fares}
    # Limita candidatos sin confundir salida del viaje con salida en la escala.
    offsets = [
        timedelta(minutes=fare.origen.minutos_desde_origen) for fare in fares
    ]
    day_start = timezone.make_aware(datetime.combine(date, time.min))
    day_end = timezone.make_aware(
        datetime.combine(date + timedelta(days=1), time.min)
    )
    trips = Viaje.objects.filter(
        estado=Viaje.Estado.PROGRAMADO,
        ruta_id__in=fares_by_route,
        fecha_hora_salida__gte=day_start.astimezone(UTC) - max(offsets),
        fecha_hora_salida__lt=day_end.astimezone(UTC) - min(offsets),
    ).select_related("ruta", "bus").order_by("fecha_hora_salida", "pk")
    results = []
    for trip in trips:
        fare = fares_by_route[trip.ruta_id]
        departure = timezone.localtime(
            trip.fecha_hora_salida
            + timedelta(minutes=fare.origen.minutos_desde_origen)
        )
        if departure.date() != date:
            continue
        try:
            available = get_available_seats(
                viaje=trip, origen=fare.origen, destino=fare.destino,
            ).count()
        except InvalidSegmentError:
            continue
        results.append({
            "trip_id": trip.pk,
            "route": {"id": trip.ruta_id, "name": trip.ruta.nombre},
            "origin": {"id": origin.pk, "name": origin.nombre},
            "destination": {"id": destination.pk, "name": destination.nombre},
            "departure_datetime": departure,
            "arrival_datetime": timezone.localtime(
                trip.fecha_hora_salida
                + timedelta(minutes=fare.destino.minutos_desde_origen)
            ),
            "price": fare.precio,
            "available_seats": available,
        })
    return sorted(results, key=lambda result: (
        result["departure_datetime"], result["trip_id"],
    ))
