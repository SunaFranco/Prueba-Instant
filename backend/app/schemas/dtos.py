from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------------------
# DTOs de Autenticación
# ------------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único")
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña de al menos 6 caracteres")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("El nombre de usuario solo puede contener letras, números, guiones y guiones bajos")
        return v

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: Optional[str] = None

# ------------------------------------------------------------------------------
# DTOs de Películas
# ------------------------------------------------------------------------------
class MovieDto(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = ""
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    genres: Optional[List[str]] = []
    vote_average: Optional[float] = 0.0

class MovieListResponse(BaseModel):
    page: int
    total_pages: int
    total_results: int
    results: List[MovieDto]

# ------------------------------------------------------------------------------
# DTOs de Me Gusta
# ------------------------------------------------------------------------------
class LikeCreateRequest(BaseModel):
    title: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    genres: Optional[List[str]] = []
    vote_average: Optional[float] = 0.0

class UserLikeItem(BaseModel):
    id: str
    tmdb_id: int
    title: str
    overview: Optional[str] = ""
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    genres: Optional[List[str]] = []
    vote_average: Optional[float] = 0.0
    created_at: Optional[str] = None

# ------------------------------------------------------------------------------
# DTOs de Recomendación e Inferencia LLM
# ------------------------------------------------------------------------------
class GroqRecommendationOutput(BaseModel):
    """Esquema estricto exigido al modelo de Groq vía Structured Outputs."""
    title: str = Field(..., description="Título exacto de la película recomendada")
    release_year: Optional[int] = Field(None, description="Año de estreno aproximado")
    rationale: str = Field(..., description="Justificación detallada y personalizada de la recomendación")
    genres: Optional[List[str]] = Field(default=[], description="Géneros principales de la película")

class RecommendationJobPayload(BaseModel):
    job_id: str
    user_id: str
    created_at: str

class RecommendationStatusResponse(BaseModel):
    job_id: str
    status: str
    recommendation: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
