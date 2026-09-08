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

## Backend local

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Para esta modalidad, PostgreSQL debe estar disponible y `DB_HOST=localhost` en
`backend/.env`. Los valores por defecto son exclusivamente de desarrollo; use
una `SECRET_KEY` segura y `DEBUG=False` fuera de ese entorno.

## Docker

```bash
docker compose up --build
```

Compose levanta PostgreSQL 16 y el backend con Gunicorn, aplica las migraciones
y publica la documentación en `http://localhost:8000/api/docs/`. No es necesario
crear un archivo `.env`: Compose incluye valores de desarrollo reemplazables
mediante variables de entorno. Dentro de Docker, `DB_HOST` es `db`.

## Tests

Con PostgreSQL disponible y las variables de `backend/.env` configuradas:

```bash
cd backend
pip install -r requirements-dev.txt
python manage.py test --noinput
```

## Coverage

```bash
cd backend
coverage erase
coverage run manage.py test --noinput
coverage report -m
coverage report --fail-under=60
```

El umbral mínimo reproducible del proyecto es 60%.

## CI

GitHub Actions ejecuta la suite completa sobre PostgreSQL 16, valida una
cobertura mínima de 60% y realiza un smoke test HTTP del stack Docker.

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

La app queda en `http://localhost:5173/`, configurada con CORS para comunicarse
con el backend.
