import requests

from .base import ResolvedProduct, Resolver

KNOWN = {
    "bitcoin": "bitcoin", "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "solana": "solana", "sol": "solana",
    "cardano": "cardano", "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "ripple": "ripple", "xrp": "ripple",
}


class CoinGeckoResolver(Resolver):
    name = "coingecko"

    def can_handle(self, raw: str) -> bool:
        s = raw.strip().lower().replace("coingecko:", "")
        return s in KNOWN

    def resolve(self, raw: str) -> ResolvedProduct | None:
        s = raw.strip().lower().replace("coingecko:", "")
        coin_id = KNOWN.get(s, s)
        try:
            r = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "false",
                    "developer_data": "false",
                },
                timeout=8,
            )
            if r.status_code != 200:
                return None
            info = r.json()
            return ResolvedProduct(
                canonical_type="crypto",
                primary_id=info["id"],
                title=info["name"],
                brand=info.get("symbol", "").upper(),
                image_url=info.get("image", {}).get("small", ""),
                attributes={"symbol": info.get("symbol", "").upper()},
            )
        except requests.RequestException:
            return None
