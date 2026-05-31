import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"


async def geocode_address(
    address: str,
    client: httpx.AsyncClient | None = None,
) -> tuple[float, float] | None:
    if not address or not address.strip():
        return None

    if not settings.kakao_rest_api_key:
        return None

    headers = {"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"}
    params = {"query": address}

    try:
        if client is None:
            async with httpx.AsyncClient() as c:
                response = await c.get(KAKAO_GEOCODE_URL, params=params, headers=headers)
        else:
            response = await client.get(KAKAO_GEOCODE_URL, params=params, headers=headers)

        if response.status_code != 200:
            return None

        documents = response.json()["documents"]
        if not documents:
            return None

        doc = documents[0]
        return float(doc["y"]), float(doc["x"])
    except Exception:
        logger.exception("geocode_address failed", address=address)
        return None
