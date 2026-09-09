# Frontend

Base React + TypeScript + Vite del sistema de pasajes interurbanos.

```bash
cp .env.example .env
npm install
npm run dev
```

La variable `VITE_API_URL` apunta por defecto a
`http://localhost:8000/api/v1`.

La autenticación académica persiste los tokens JWT en `localStorage`. Para un
entorno productivo debe evaluarse una estrategia basada en cookies seguras
HttpOnly junto con las protecciones correspondientes en el backend.
