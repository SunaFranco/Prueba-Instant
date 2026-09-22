# Especificación de Endpoints de la API (RESTful)

**Base URL:** `http://localhost:5000/api`

---

## 1. Módulo de Autenticación (`/auth`)

### `POST /auth/register`
Crea una nueva cuenta de usuario.
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "username": "cinefilo123",
    "password": "PasswordSegura123!"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "message": "Usuario registrado exitosamente",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      "username": "cinefilo123"
    }
  }
  ```

### `POST /auth/login`
Inicia sesión con credenciales existentes.
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "username": "cinefilo123",
    "password": "PasswordSegura123!"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      "username": "cinefilo123"
    }
  }
  ```

### `GET /auth/me`
Obtiene los datos del usuario autenticado.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "username": "cinefilo123",
    "created_at": "2026-09-15T15:00:00Z"
  }
  ```

---

## 2. Módulo de Películas (`/movies`)

### `GET /movies`
Lista películas populares o busca por título con soporte de paginación y caché en Redis.
* **Query Params:**
  * `page` (opcional, default: `1`): Número de página.
  * `query` (opcional): Término de búsqueda por título.
* **Response (200 OK):**
  ```json
  {
    "page": 1,
    "total_pages": 500,
    "total_results": 10000,
    "results": [
      {
        "tmdb_id": 27205,
        "title": "Inception",
        "overview": "Cobb, a skilled thief who commits corporate espionage...",
        "poster_path": "/ljsZTbVsrQSqZgWeep2P1P2Yum4.jpg",
        "release_date": "2010-07-15",
        "vote_average": 8.4,
        "genres": ["Action", "Science Fiction", "Adventure"]
      }
    ]
  }
  ```

### `GET /movies/<int:tmdb_id>`
Obtiene el detalle completo de una película de TMDB.
* **Response (200 OK):**
  ```json
  {
    "tmdb_id": 27205,
    "title": "Inception",
    "overview": "Cobb, a skilled thief...",
    "poster_path": "/ljsZTbVsrQSqZgWeep2P1P2Yum4.jpg",
    "release_date": "2010-07-15",
    "vote_average": 8.4,
    "genres": ["Action", "Science Fiction", "Adventure"]
  }
  ```

---

## 3. Módulo de 'Me Gusta' / Favoritos (`/likes`)

### `GET /likes`
Lista todas las películas que le gustaron al usuario autenticado.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "likes": [
      {
        "like_id": "7b8f9e01-1234-5678-abcd-ef0123456789",
        "tmdb_id": 27205,
        "title": "Inception",
        "overview": "Cobb, a skilled thief...",
        "poster_path": "/ljsZTbVsrQSqZgWeep2P1P2Yum4.jpg",
        "release_date": "2010-07-15",
        "created_at": "2026-09-15T15:30:00Z"
      }
    ]
  }
  ```

### `POST /likes/<int:tmdb_id>`
Agrega una película a la lista de favoritos del usuario.
* **Headers:** `Authorization: Bearer <token>`
* **Request Body (Opcional si se envían metadatos para caché):**
  ```json
  {
    "title": "Inception",
    "overview": "Cobb, a skilled thief...",
    "poster_path": "/ljsZTbVsrQSqZgWeep2P1P2Yum4.jpg",
    "release_date": "2010-07-15",
    "vote_average": 8.4,
    "genres": ["Action", "Science Fiction"]
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "message": "Película agregada a favoritos exitosamente",
    "tmdb_id": 27205
  }
  ```

### `DELETE /likes/<int:tmdb_id>`
Elimina una película de la lista de favoritos.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "message": "Película eliminada de favoritos exitosamente",
    "tmdb_id": 27205
  }
  ```

---

## 4. Módulo de Recomendaciones Inteligentes (`/recommendations`)

### `POST /recommendations/request`
Encola una nueva solicitud de recomendación para el usuario autenticado.
* **Headers:** `Authorization: Bearer <token>`
* **Response (202 Accepted):**
  ```json
  {
    "message": "Solicitud de recomendación encolada exitosamente",
    "job_id": "rec_job_9a8b7c6d5e4f",
    "status": "PENDING"
  }
  ```

### `GET /recommendations/status/<string:job_id>`
Consulta el estado de procesamiento del trabajo encolado. Cuando finaliza, retorna la lista de las 3 recomendaciones deduplicadas.
* **Headers:** `Authorization: Bearer <token>`
* **Response cuando está en proceso (200 OK):**
  ```json
  {
    "job_id": "rec_job_9a8b7c6d5e4f",
    "status": "PROCESSING",
    "recommendations": []
  }
  ```
* **Response cuando finalizó (200 OK):**
  ```json
  {
    "job_id": "rec_job_9a8b7c6d5e4f",
    "status": "COMPLETED",
    "recommendations": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "job_id": "rec_job_9a8b7c6d5e4f",
        "recommended_title": "Interstellar",
        "recommended_tmdb_id": 157336,
        "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "overview": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
        "rationale": "Dado que te fascinó 'Inception' por sus giros conceptuales y su trama de ciencia ficción profunda, 'Interstellar' del mismo director Christopher Nolan te cautivará con su exploración del tiempo y la relatividad.",
        "vote_average": 8.4,
        "completed_at": "2026-09-15T15:35:10Z"
      },
      {
        "id": "a12bc34d-67ef-4890-b123-1f23c4d5e680",
        "job_id": "rec_job_9a8b7c6d5e4f_2",
        "recommended_title": "Blade Runner 2049",
        "recommended_tmdb_id": 335984,
        "poster_path": "/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
        "overview": "Thirty years after the events of the first film, a new Blade Runner discovers a long-buried secret.",
        "rationale": "Una experiencia visual impresionante que profundiza en dilemas existenciales similares a tu historial cinematográfico.",
        "vote_average": 7.9,
        "completed_at": "2026-09-15T15:35:10Z"
      },
      {
        "id": "c34de56f-78ab-4901-c234-2a34b5c6d791",
        "job_id": "rec_job_9a8b7c6d5e4f_3",
        "recommended_title": "Arrival",
        "recommended_tmdb_id": 329865,
        "poster_path": "/x2O0hv9N7n845gq3BflF1eYyA2Z.jpg",
        "overview": "Taking place after alien spacecrafts land around the world, a linguist is recruited to communicate.",
        "rationale": "Perfecta para quienes aprecian historias reflexivas y estructuras narrativas no lineales.",
        "vote_average": 7.6,
        "completed_at": "2026-09-15T15:35:10Z"
      }
    ]
  }
  ```

### `GET /recommendations`
Lista el historial completo de recomendaciones generadas previamente para el usuario.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "recommendations": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "job_id": "rec_job_9a8b7c6d5e4f",
        "recommended_title": "Interstellar",
        "recommended_tmdb_id": 157336,
        "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "rationale": "Dado que te fascinó Inception...",
        "created_at": "2026-09-15T15:35:00Z"
      }
    ]
  }
  ```

### `DELETE /recommendations/<string:rec_id>`
Elimina una recomendación del historial del usuario (por ejemplo, al convertirla en favorito o descartarla).
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "message": "Recomendación eliminada exitosamente",
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
  ```

