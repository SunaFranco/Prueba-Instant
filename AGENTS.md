# Contexto para Agentes de Desarrollo y LLMs

## Descripción del Proyecto
Sistema de recomendación de películas basado en inteligencia artificial para la prueba técnica de **Instant**.
Combina el catálogo de películas de **The Movie Database (TMDB)** con inferencia ultrarrápida de **Groq Cloud API** (`llama-3.3-70b-versatile`), desacoplado mediante una cola en **Redis** con control estricto de **Rate Limiting (Token Bucket)** en un worker de Python.

## Estructura de Capas del Backend (Python / Flask)
* `app/routes/`: Controladores HTTP RESTful (Blueprints de Flask). Validan DTOs con Pydantic y delegan la lógica a los servicios.
* `app/services/`: Lógica de negocio (Autenticación, llamadas a TMDB, cálculo de prompts, persistencia de Likes).
* `app/db/`: Inicialización del cliente Supabase (`supabase-py`) y conexión PostgreSQL.
* `app/queue/`: Productor de tareas a Redis y algoritmo Token Bucket de Rate Limiting.
* `worker.py`: Proceso consumidor desacoplado que extrae de Redis, consulta a Groq con rate limiting y actualiza Supabase.

## Principios y Convenciones de Código
1. **Clean Code & Tipado:** Utilizar Type Hints en funciones de Python y validadores Pydantic v2 en DTOs.
2. **Modularidad:** Mantener los Blueprints limpios, sin consultas directas a base de datos ni llamadas HTTP externas dentro de las rutas.
3. **Manejo de Errores:** Retornar códigos de estado HTTP semánticos (200, 201, 202, 400, 401, 404, 429, 500) con mensajes JSON consistentes `{ "error": "...", "details": "..." }`.
4. **Resiliencia Externa:** Toda llamada a TMDB o Groq debe incluir timeouts, manejo de excepciones y reintentos en caso de rate limits (`429`).
