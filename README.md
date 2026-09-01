# Sistema de gestión y venta de pasajes de buses

Proyecto académico: monolito modular para gestionar rutas de buses con
múltiples escalas y vender pasajes por tramo (ej. La Serena → Antofagasta
dentro de un recorrido Santiago → La Serena → Copiapó → Antofagasta → Arica),
validando disponibilidad de asientos y evitando reservas duplicadas.

## Arquitectura

- **Backend:** Python + Django REST Framework — monolito modular (sin
  microservicios), con las responsabilidades separadas en apps de Django.
- **Frontend:** React + TypeScript (Vite).
- **Base de datos:** PostgreSQL.

## Estructura del repo

```
sistema-buses/
├── backend/
│   ├── config/        # settings, urls, wsgi/asgi
│   ├── usuarios/       # autenticación y roles
│   ├── flota/          # buses y asientos
│   ├── rutas/          # rutas y paradas ordenadas
│   ├── viajes/         # instancias de un viaje (ruta + bus + fecha)
│   ├── ventas/         # búsqueda por tramo, reservas y boletos
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/         # cliente HTTP hacia el backend
│   │   ├── pages/        # pantallas (buscar, seleccionar asiento, confirmar)
│   │   ├── components/
│   │   └── types/
│   └── .env.example
└── docker-compose.yml   # levanta PostgreSQL para desarrollo local
```

## Cómo levantar el proyecto

### 1. Base de datos

Con Docker instalado:

```bash
docker compose up -d
```

Esto levanta PostgreSQL en `localhost:5432` con la base `sistema_buses`
(usuario `postgres`, password `postgres` — solo para desarrollo local).

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La API queda en `http://localhost:8000/` y el admin de Django en
`http://localhost:8000/admin/`.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

La app queda en `http://localhost:5173/`, ya configurada con CORS para
hablar con el backend.

## Estado actual

Estructura inicial del proyecto: apps de Django creadas y registradas,
settings.py configurado para PostgreSQL vía variables de entorno, CORS
habilitado, y el scaffold de React + TypeScript con la capa de cliente API
lista. Aún no hay modelos de datos ni endpoints — ese es el siguiente paso
(empezando por `rutas` y `viajes`, y la lógica de disponibilidad por tramo
en `ventas`).
