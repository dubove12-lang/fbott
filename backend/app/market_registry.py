import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .hyperliquid_client import HyperliquidClient


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "backend" / "data"
REGISTRY_PATH = DATA_DIR / "market_registry.json"

# This dashboard's TradFi universe should be driven primarily by HIP-3 XYZ DEX metadata,
# not by a hand-maintained list of tickers.
_DEFAULT_TRADFI_DEXES = "xyz"
_DEFAULT_TRADFI_PREFIXES = "XYZ"


_CACHE: Dict[str, Any] = {
    "ts": 0.0,
    "registry": None,
}


def normalize_symbol(symbol: str) -> str:
    raw = str(symbol or "").upper().strip()
    raw = raw.replace("-", "_").replace("/", "_")
    if ":" in raw:
        raw = raw.split(":")[-1]
    if raw.startswith("PERP_"):
        raw = raw[5:]
    if raw.endswith("_PERP"):
        raw = raw[:-5]
    return raw


def raw_symbol(symbol: str) -> str:
    return str(symbol or "").upper().strip()


def manual_tradfi_symbols() -> Set[str]:
    # Optional overrides only. This should not be the main source.
    env_value = os.getenv("MARKET_TYPE_TRADFI_COINS", "")
    return {normalize_symbol(x) for x in env_value.split(",") if x.strip()}


def tradfi_prefixes() -> Set[str]:
    env_value = os.getenv("MARKET_TYPE_TRADFI_PREFIXES", _DEFAULT_TRADFI_PREFIXES)
    return {raw_symbol(x) for x in env_value.split(",") if x.strip()}


def configured_tradfi_dexes() -> Set[str]:
    env_value = os.getenv("MARKET_TYPE_TRADFI_DEXES", _DEFAULT_TRADFI_DEXES)
    return {str(x).strip().lower() for x in env_value.split(",") if str(x).strip()}


def is_tradfi_dex_name(dex_name: str, dex_obj: Optional[Dict[str, Any]] = None) -> bool:
    name = str(dex_name or "").strip().lower()
    if name in configured_tradfi_dexes():
        return True

    haystack = name
    if isinstance(dex_obj, dict):
        haystack += " " + " ".join(str(v).lower() for v in dex_obj.values() if isinstance(v, (str, int, float, bool)))

    return "xyz" in haystack


def classify_symbol(symbol: str, registry: Optional[Dict[str, Any]] = None, dex: Optional[str] = None) -> str:
    raw = raw_symbol(symbol)
    norm = normalize_symbol(symbol)

    if dex and is_tradfi_dex_name(dex):
        return "tradfi"

    if norm in manual_tradfi_symbols():
        return "tradfi"

    for prefix in tradfi_prefixes():
        if prefix and (raw.startswith(prefix) or raw.startswith(prefix + ":") or (prefix + ":") in raw):
            return "tradfi"

    if registry:
        index = registry.get("index") or {}
        item = index.get(raw) or index.get(norm)
        if isinstance(item, dict) and item.get("market_type"):
            return str(item["market_type"])

    return "crypto"


def tradfi_asset_class(symbol: str, dex: Optional[str] = None) -> str:
    if dex and is_tradfi_dex_name(dex):
        return "xyz_dex"
    raw = raw_symbol(symbol)
    norm = normalize_symbol(symbol)
    if raw.startswith("XYZ") or "XYZ:" in raw:
        return "xyz_dex"
    if norm in manual_tradfi_symbols():
        return "manual_tradfi"
    return "crypto"


def _extract_universe_and_contexts(payload: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if isinstance(payload, list) and len(payload) >= 2:
        meta = payload[0] if isinstance(payload[0], dict) else {}
        ctxs = payload[1] if isinstance(payload[1], list) else []
        universe = meta.get("universe") or []
        return universe if isinstance(universe, list) else [], ctxs

    if isinstance(payload, dict):
        universe = payload.get("universe") or []
        return universe if isinstance(universe, list) else [], []

    return [], []


def _dex_entries_from_perp_dexs(payload: Any) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return entries

    for idx, item in enumerate(payload):
        if item is None:
            continue
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            out = dict(item)
            out["dex_index"] = idx
            entries.append(out)
    return entries


def _fetch_dex_meta(client: HyperliquidClient, dex: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    try:
        payload = client.meta_and_asset_ctxs(dex=dex)
        return _extract_universe_and_contexts(payload)
    except Exception:
        try:
            payload = client.meta(dex=dex)
            return _extract_universe_and_contexts(payload)
        except Exception:
            return [], []


def build_registry_from_hyperliquid() -> Dict[str, Any]:
    client = HyperliquidClient()

    dex_entries: List[Dict[str, Any]] = []
    try:
        dex_entries = _dex_entries_from_perp_dexs(client.perp_dexs())
    except Exception as exc:
        dex_entries = []
        perp_dexs_error = str(exc)
    else:
        perp_dexs_error = None

    tradfi_dex_entries = [d for d in dex_entries if is_tradfi_dex_name(str(d.get("name") or ""), d)]

    # Always include configured dex names even if perpDexs failed.
    existing = {str(d.get("name") or "").lower() for d in tradfi_dex_entries}
    for dex_name in sorted(configured_tradfi_dexes()):
        if dex_name not in existing:
            tradfi_dex_entries.append({"name": dex_name, "source": "configured_env"})

    items: List[Dict[str, Any]] = []
    index: Dict[str, Dict[str, Any]] = {}
    errors: Dict[str, str] = {}

    for dex_obj in tradfi_dex_entries:
        dex_name = str(dex_obj.get("name") or "").strip()
        if not dex_name:
            continue

        universe, ctxs = _fetch_dex_meta(client, dex_name)
        ctx_by_index = {i: ctx for i, ctx in enumerate(ctxs) if isinstance(ctx, dict)}

        if not universe:
            errors[dex_name] = "empty_or_failed_meta"
            continue

        for i, asset in enumerate(universe):
            if not isinstance(asset, dict):
                continue

            name = str(asset.get("name") or asset.get("coin") or asset.get("symbol") or "").strip()
            if not name:
                continue

            norm = normalize_symbol(name)
            raw = raw_symbol(name)
            qualified = f"{dex_name}:{name}"
            ctx = ctx_by_index.get(i, {})

            item = {
                "raw_symbol": name,
                "symbol": norm,
                "qualified_symbol": qualified,
                "dex": dex_name,
                "market_type": "tradfi",
                "asset_class": "xyz_dex",
                "source": "hyperliquid_perpDexs_meta",
                "asset_index": i,
                "sz_decimals": asset.get("szDecimals"),
                "max_leverage": asset.get("maxLeverage"),
                "only_isolated": asset.get("onlyIsolated"),
                "is_delisted": asset.get("isDelisted", False),
                "mark_px": ctx.get("markPx") or ctx.get("midPx"),
                "open_interest": ctx.get("openInterest"),
                "day_volume": ctx.get("dayNtlVlm") or ctx.get("dayBaseVlm"),
            }
            items.append(item)

            # Index all common forms seen in positions / ccxt / UI.
            for key in {
                raw,
                norm,
                raw_symbol(qualified),
                normalize_symbol(qualified),
                raw_symbol(f"{dex_name}-{name}"),
                normalize_symbol(f"{dex_name}-{name}"),
            }:
                if key:
                    index[key] = item

    # Manual overrides remain fallback.
    for sym in sorted(manual_tradfi_symbols()):
        if sym in index:
            continue
        item = {
            "raw_symbol": sym,
            "symbol": sym,
            "qualified_symbol": sym,
            "dex": "manual",
            "market_type": "tradfi",
            "asset_class": "manual_tradfi",
            "source": "manual_env_override",
        }
        items.append(item)
        index[sym] = item

    registry = {
        "version": 2,
        "generated_at": int(time.time()),
        "source": "hyperliquid_perpDexs_xyz_dex",
        "count": len(items),
        "items": items,
        "index": index,
        "tradfi_dexes": sorted({str(d.get("name") or "").strip() for d in tradfi_dex_entries if str(d.get("name") or "").strip()}),
        "configured_tradfi_dexes": sorted(configured_tradfi_dexes()),
        "tradfi_prefixes": sorted(tradfi_prefixes()),
        "manual_tradfi_symbols": sorted(manual_tradfi_symbols()),
        "perp_dexs_count": len(dex_entries),
        "perp_dexs_error": perp_dexs_error,
        "dex_meta_errors": errors,
    }
    return registry


def save_registry(registry: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    persist = dict(registry)
    persist.pop("index", None)
    REGISTRY_PATH.write_text(json.dumps(persist, indent=2, sort_keys=True), encoding="utf-8")


def _index_registry(registry: Dict[str, Any]) -> Dict[str, Any]:
    if registry.get("index"):
        return registry

    index: Dict[str, Dict[str, Any]] = {}
    for item in registry.get("items") or []:
        if not isinstance(item, dict):
            continue
        raw = raw_symbol(item.get("raw_symbol") or item.get("symbol") or "")
        norm = normalize_symbol(item.get("symbol") or raw)
        dex = str(item.get("dex") or "").strip()
        qualified = str(item.get("qualified_symbol") or "").strip()
        for key in {raw, norm, raw_symbol(qualified), normalize_symbol(qualified), raw_symbol(f"{dex}:{raw}"), normalize_symbol(f"{dex}:{raw}")}:
            if key:
                index[key] = item

    registry["index"] = index
    return registry


def load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return _index_registry(data)
        except Exception:
            pass

    # Fallback registry knows dex names/prefixes but no full live ticker list.
    registry = {
        "version": 2,
        "generated_at": 0,
        "source": "fallback_configured_xyz_dex",
        "count": 0,
        "items": [],
        "tradfi_dexes": sorted(configured_tradfi_dexes()),
        "configured_tradfi_dexes": sorted(configured_tradfi_dexes()),
        "manual_tradfi_symbols": sorted(manual_tradfi_symbols()),
        "tradfi_prefixes": sorted(tradfi_prefixes()),
    }
    return _index_registry(registry)


def get_registry(force_refresh: bool = False) -> Dict[str, Any]:
    ttl = int(os.getenv("MARKET_REGISTRY_CACHE_TTL_SECONDS", "3600"))
    now = time.time()

    if (
        not force_refresh
        and _CACHE.get("registry") is not None
        and (now - float(_CACHE.get("ts", 0))) < ttl
    ):
        return _CACHE["registry"]

    auto_refresh = os.getenv("MARKET_REGISTRY_AUTO_REFRESH", "false").lower() in ("1", "true", "yes", "on")
    max_age = int(os.getenv("MARKET_REGISTRY_MAX_AGE_SECONDS", "86400"))

    registry = load_registry()
    age = now - float(registry.get("generated_at") or 0)

    if force_refresh or (auto_refresh and age > max_age):
        try:
            registry = build_registry_from_hyperliquid()
            save_registry(registry)
        except Exception as exc:
            registry = load_registry()
            registry["refresh_error"] = str(exc)

    registry = _index_registry(registry)
    _CACHE["registry"] = registry
    _CACHE["ts"] = now
    return registry


def refresh_registry() -> Dict[str, Any]:
    registry = build_registry_from_hyperliquid()
    save_registry(registry)
    registry = _index_registry(registry)
    _CACHE["registry"] = registry
    _CACHE["ts"] = time.time()
    return registry


def classify_coin(coin: str, dex: Optional[str] = None) -> str:
    registry = get_registry(force_refresh=False)
    return classify_symbol(coin, registry=registry, dex=dex)


def tradfi_dex_names() -> List[str]:
    registry = get_registry(force_refresh=False)
    names = set(configured_tradfi_dexes())
    for dex in registry.get("tradfi_dexes") or []:
        if str(dex).strip():
            names.add(str(dex).strip().lower())
    return sorted(names)


def registry_summary() -> Dict[str, Any]:
    registry = get_registry(force_refresh=False)
    items = registry.get("items") or []
    tradfi = [x for x in items if isinstance(x, dict) and x.get("market_type") == "tradfi"]
    crypto = [x for x in items if isinstance(x, dict) and x.get("market_type") == "crypto"]

    dex_counts: Dict[str, int] = {}
    for item in tradfi:
        dex = str(item.get("dex") or "unknown")
        dex_counts[dex] = dex_counts.get(dex, 0) + 1

    return {
        "source": registry.get("source"),
        "generated_at": registry.get("generated_at"),
        "count": len(items),
        "tradfi_count": len(tradfi),
        "crypto_count": len(crypto),
        "dex_counts": dex_counts,
        "tradfi_dexes": registry.get("tradfi_dexes", []),
        "configured_tradfi_dexes": registry.get("configured_tradfi_dexes", []),
        "tradfi_symbols": [x.get("qualified_symbol") or x.get("raw_symbol") for x in tradfi],
        "manual_tradfi_symbols": registry.get("manual_tradfi_symbols", []),
        "tradfi_prefixes": registry.get("tradfi_prefixes", []),
        "perp_dexs_count": registry.get("perp_dexs_count"),
        "perp_dexs_error": registry.get("perp_dexs_error"),
        "dex_meta_errors": registry.get("dex_meta_errors"),
        "refresh_error": registry.get("refresh_error"),
    }
