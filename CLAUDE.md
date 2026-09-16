# Guía de Desarrollo Rápido y Atajos (CLAUDE.md)

## Comandos Principales

### Despliegue con Docker Compose
```bash
# Levantar todo el stack (Redis, Backend API, Worker, Frontend)
docker compose up --build

# Ver logs en tiempo real
docker compose logs -f

# Detener los contenedores
docker compose down
```

### Backend (Desarrollo Local con Python)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Ejecutar el servidor API
python run.py

# Ejecutar el worker asíncrono
python worker.py

# Ejecutar pruebas unitarias
pytest
```

### Frontend (Desarrollo Local con Vite)
```bash
cd frontend
npm install
npm run dev
```
