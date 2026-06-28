import time
from typing import Any, Dict, Optional

import requests


# Priority 1: local/manual overrides for common and Hyperliquid-specific tickers.
TOKEN_ICON_OVERRIDES = {
    "BTC": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png",
    "ETH": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
    "SOL": "https://assets.coingecko.com/coins/images/4128/small/solana.png",
    "HYPE": "https://assets.coingecko.com/coins/images/50882/small/hyperliquid.jpg",
    "DOGE": "https://assets.coingecko.com/coins/images/5/small/dogecoin.png",
    "SUI": "https://assets.coingecko.com/coins/images/26375/small/sui_asset.jpeg",
    "LINK": "https://assets.coingecko.com/coins/images/877/small/chainlink-new-logo.png",
    "XRP": "https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png",
    "WLD": "https://assets.coingecko.com/coins/images/31069/small/worldcoin.jpeg",
    "TRX": "https://assets.coingecko.com/coins/images/1094/small/tron-logo.png",
    "AVAX": "https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png",
    "BNB": "https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png",
    "ARB": "https://assets.coingecko.com/coins/images/16547/small/arb.jpg",
    "OP": "https://assets.coingecko.com/coins/images/25244/small/Optimism.png",
    "FARTCOIN": "https://assets.coingecko.com/coins/images/50891/small/fart.jpg",
    "ZEC": "https://assets.coingecko.com/coins/images/486/small/circle-zcash-color.png",
    "TAO": "https://assets.coingecko.com/coins/images/28452/small/ARUsPeNQ_400x400.jpeg",
    "TON": "https://assets.coingecko.com/coins/images/17980/small/ton_symbol.png",
    "NEAR": "https://assets.coingecko.com/coins/images/10365/small/near.jpg",
    "ADA": "https://assets.coingecko.com/coins/images/975/small/cardano.png",
    "ICP": "https://assets.coingecko.com/coins/images/14495/small/Internet_Computer_logo.png",
    "SEI": "https://assets.coingecko.com/coins/images/28205/small/Sei_Logo_-_Transparent.png",
    "PUMP": "https://assets.coingecko.com/coins/images/34478/small/pump.png",
    "ATOM": "https://assets.coingecko.com/coins/images/1481/small/cosmos_hub.png",
    "LTC": "https://assets.coingecko.com/coins/images/2/small/litecoin.png",
    "INJ": "https://assets.coingecko.com/coins/images/12882/small/Secondary_Symbol.png",
    "APE": "https://assets.coingecko.com/coins/images/24383/small/apecoin.jpg",
    "LDO": "https://assets.coingecko.com/coins/images/13573/small/Lido_DAO.png",
    "PEPE": "https://assets.coingecko.com/coins/images/29850/small/pepe-token.jpeg",
    "KPEPE": "https://assets.coingecko.com/coins/images/29850/small/pepe-token.jpeg",
}


_ICON_CACHE: Dict[str, Dict[str, Any]] = {}
_CRYPTOCOMPARE_COINLIST_CACHE: Dict[str, Any] = {"ts": 0.0, "data": None}
_ICON_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
_REQUEST_TIMEOUT_SECONDS = 3.0


def normalize_coin_symbol(coin: str) -> str:
    if not coin:
        return ""
    value = str(coin).strip().upper()
    if ":" in value:
        value = value.split(":")[-1]
    value = value.replace("/", "").replace("-", "").replace("_", "")
    return value


def _cache_get(symbol: str) -> Optional[str]:
    item = _ICON_CACHE.get(symbol)
    if not item:
        return None
    if time.time() - float(item.get("ts", 0)) > _ICON_CACHE_TTL_SECONDS:
        return None
    return item.get("url")


def _cache_set(symbol: str, url: Optional[str], source: str):
    _ICON_CACHE[symbol] = {
        "url": url or "",
        "source": source,
        "ts": time.time(),
    }


def _coingecko_search_icon(symbol: str) -> Optional[str]:
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/search",
            params={"query": symbol},
            timeout=_REQUEST_TIMEOUT_SECONDS,
            headers={"accept": "application/json"},
        )
        if response.status_code != 200:
            return None
        data = response.json()
        coins = data.get("coins") if isinstance(data, dict) else None
        if not isinstance(coins, list):
            return None

        exact = None
        for coin in coins:
            if not isinstance(coin, dict):
                continue
            if str(coin.get("symbol") or "").upper() == symbol:
                exact = coin
                break

        chosen = exact or (coins[0] if coins else None)
        if not isinstance(chosen, dict):
            return None
        image = chosen.get("large") or chosen.get("thumb")
        return image if isinstance(image, str) and image.startswith("http") else None
    except Exception:
        return None


def _cryptocompare_coinlist() -> Optional[Dict[str, Any]]:
    now = time.time()
    cached = _CRYPTOCOMPARE_COINLIST_CACHE.get("data")
    if cached is not None and now - float(_CRYPTOCOMPARE_COINLIST_CACHE.get("ts") or 0) < _ICON_CACHE_TTL_SECONDS:
        return cached

    try:
        response = requests.get(
            "https://min-api.cryptocompare.com/data/all/coinlist",
            timeout=_REQUEST_TIMEOUT_SECONDS,
            headers={"accept": "application/json"},
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        data = payload.get("Data") if isinstance(payload, dict) else None
        if isinstance(data, dict):
            _CRYPTOCOMPARE_COINLIST_CACHE["data"] = data
            _CRYPTOCOMPARE_COINLIST_CACHE["ts"] = now
            return data
    except Exception:
        return None
    return None


def _cryptocompare_icon(symbol: str) -> Optional[str]:
    data = _cryptocompare_coinlist()
    if not data:
        return None
    item = data.get(symbol)
    if not isinstance(item, dict):
        return None
    image_path = item.get("ImageUrl")
    if isinstance(image_path, str) and image_path:
        if image_path.startswith("http"):
            return image_path
        return "https://www.cryptocompare.com" + image_path
    return None


def resolve_token_icon(coin: str) -> Dict[str, Any]:
    symbol = normalize_coin_symbol(coin)
    if not symbol:
        return {"coin": coin, "symbol": symbol, "url": "", "source": "empty"}

    override = TOKEN_ICON_OVERRIDES.get(symbol)
    if override:
        return {"coin": coin, "symbol": symbol, "url": override, "source": "override"}

    cached = _cache_get(symbol)
    if cached:
        return {"coin": coin, "symbol": symbol, "url": cached, "source": _ICON_CACHE.get(symbol, {}).get("source", "cache")}

    url = _coingecko_search_icon(symbol)
    if url:
        _cache_set(symbol, url, "coingecko_search")
        return {"coin": coin, "symbol": symbol, "url": url, "source": "coingecko_search"}

    # Common Hyperliquid k-prefix convention, e.g. kPEPE -> PEPE.
    if symbol.startswith("K") and len(symbol) > 2:
        url = TOKEN_ICON_OVERRIDES.get(symbol[1:]) or _coingecko_search_icon(symbol[1:])
        if url:
            _cache_set(symbol, url, "coingecko_k_prefix")
            return {"coin": coin, "symbol": symbol, "url": url, "source": "coingecko_k_prefix"}

    url = _cryptocompare_icon(symbol)
    if url:
        _cache_set(symbol, url, "cryptocompare")
        return {"coin": coin, "symbol": symbol, "url": url, "source": "cryptocompare"}

    _cache_set(symbol, "", "fallback")
    return {"coin": coin, "symbol": symbol, "url": "", "source": "fallback"}


def get_token_icon_url(coin: str) -> Optional[str]:
    result = resolve_token_icon(coin)
    return result.get("url") or None
