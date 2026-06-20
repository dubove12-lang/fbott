from typing import Optional


# CoinGecko image URLs for common Hyperliquid tickers.
# Unknown / Hyperliquid-only tickers fall back to the letter badge in the frontend.
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
}


def normalize_coin_symbol(coin: str) -> str:
    if not coin:
        return ""
    # Hyperliquid can include tokens like xyz:SPCX. Keep only the market suffix for mapping.
    coin = str(coin).strip().upper()
    if ":" in coin:
        coin = coin.split(":")[-1]
    return coin


def get_token_icon_url(coin: str) -> Optional[str]:
    return TOKEN_ICON_OVERRIDES.get(normalize_coin_symbol(coin))
