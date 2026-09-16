import pytest
from app import create_app
from app.config import Config
from app.schemas.dtos import RegisterRequest, GroqRecommendationOutput

class TestConfig(Config):
    TESTING = True
    FLASK_ENV = "testing"
    SUPABASE_URL = ""
    SUPABASE_KEY = ""
    TMDB_API_KEY = ""
    GROQ_API_KEY = ""

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Verifica que el endpoint /api/health responda 200."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "services" in data

def test_pydantic_dtos_validation():
    """Valida los esquemas Pydantic."""
    # Válido
    reg = RegisterRequest(username="cinefilo_99", password="PasswordSegura123")
    assert reg.username == "cinefilo_99"

    # Salida esperada de Groq
    groq_out = GroqRecommendationOutput(
        title="Dune: Part Two",
        release_year=2024,
        rationale="Por tu gusto en ciencia ficción épica.",
        genres=["Ciencia ficción", "Aventura"]
    )
    assert groq_out.title == "Dune: Part Two"
    assert groq_out.release_year == 2024
