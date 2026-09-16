-- ==============================================================================
-- Schema SQL para Supabase (PostgreSQL) - Sistema de Recomendación de Películas
-- ==============================================================================

-- 1. Extensión para UUIDs (Habilitada por defecto en Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Tabla de Usuarios
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabla de Películas (Referencia local y caché en DB)
CREATE TABLE IF NOT EXISTS movies (
    tmdb_id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    overview TEXT,
    poster_path VARCHAR(255),
    release_date VARCHAR(20),
    genres JSONB DEFAULT '[]'::jsonb,
    vote_average NUMERIC(3, 1) DEFAULT 0.0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabla de 'Me Gusta' (Likes / Favoritos)
CREATE TABLE IF NOT EXISTS user_likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tmdb_id INTEGER NOT NULL REFERENCES movies(tmdb_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_movie_like UNIQUE (user_id, tmdb_id)
);

-- 5. Tabla de Recomendaciones Generadas por el LLM (Groq)
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    recommended_tmdb_id INTEGER REFERENCES movies(tmdb_id) ON DELETE SET NULL,
    recommended_title VARCHAR(255),
    rationale TEXT,
    input_context JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 6. Índices para acelerar búsquedas y joins frecuentes
CREATE INDEX IF NOT EXISTS idx_user_likes_user_id ON user_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_likes_tmdb_id ON user_likes(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_job_id ON recommendations(job_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);

-- 7. Trigger para actualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER trigger_movies_updated_at
    BEFORE UPDATE ON movies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
