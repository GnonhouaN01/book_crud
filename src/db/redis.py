from redis.asyncio import Redis

from src.config import Config


redis_client = Redis.from_url(Config.REDIS_URL, decode_responses=True)


async def is_token_revoked(token_id: str) -> bool:
    return await redis_client.exists(f"revoked-token:{token_id}") > 0


async def revoke_token(token_id: str, expires_at: int | float) -> None:
    import time

    ttl = max(1, int(expires_at - time.time()))
    await redis_client.set(f"revoked-token:{token_id}", "1", ex=ttl)