import time
import logging
from typing import Optional
import redis
from app.config import Config

logger = logging.getLogger(__name__)

class TokenBucketRateLimiter:
    """
    Implementación del algoritmo Token Bucket sobre Redis para controlar la tasa
    de llamadas hacia la API de Groq y evitar errores 429 (Rate Limit Exceeded).
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis],
        key_prefix: str = "rate_limit:groq",
        rate_per_minute: int = 20,
        capacity: Optional[int] = None
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.rate_per_second = rate_per_minute / 60.0
        self.capacity = capacity if capacity is not None else rate_per_minute
        # Fallback en memoria si Redis no está disponible
        self._local_tokens = float(self.capacity)
        self._local_last_update = time.time()

    def acquire(self, tokens_requested: int = 1, timeout: float = 60.0) -> bool:
        """
        Bloquea hasta que haya tokens suficientes disponibles o expire el timeout.
        Retorna True si adquirió el token, False si expiró el tiempo de espera.
        """
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if self._consume(tokens_requested):
                return True
            # Esperar una fracción de tiempo antes de volver a intentar
            sleep_time = max(0.2, (1.0 / self.rate_per_second) / 2)
            time.sleep(sleep_time)

        logger.warning(f"Timeout de {timeout}s alcanzado esperando tokens en el Rate Limiter.")
        return False

    def _consume(self, tokens: int) -> bool:
        """Verifica y descuenta tokens atómicamente."""
        if self.redis is None:
            return self._consume_local(tokens)

        key_tokens = f"{self.key_prefix}:tokens"
        key_timestamp = f"{self.key_prefix}:ts"
        now = time.time()

        try:
            pipe = self.redis.pipeline()
            pipe.get(key_tokens)
            pipe.get(key_timestamp)
            stored_tokens, stored_ts = pipe.execute()

            if stored_tokens is None or stored_ts is None:
                current_tokens = float(self.capacity)
                last_time = now
            else:
                last_time = float(stored_ts)
                delta = max(0.0, now - last_time)
                # Regeneración de tokens proporcional al tiempo transcurrido
                current_tokens = min(float(self.capacity), float(stored_tokens) + delta * self.rate_per_second)

            if current_tokens >= tokens:
                new_tokens = current_tokens - tokens
                pipe = self.redis.pipeline()
                pipe.set(key_tokens, new_tokens)
                pipe.set(key_timestamp, now)
                pipe.execute()
                return True
            else:
                return False
        except redis.RedisError as e:
            logger.warning(f"Fallo en Redis al consultar tokens ({str(e)}). Usando fallback local.")
            return self._consume_local(tokens)

    def _consume_local(self, tokens: int) -> bool:
        """Fallback local en memoria."""
        now = time.time()
        delta = max(0.0, now - self._local_last_update)
        self._local_tokens = min(float(self.capacity), self._local_tokens + delta * self.rate_per_second)
        self._local_last_update = now

        if self._local_tokens >= tokens:
            self._local_tokens -= tokens
            return True
        return False
