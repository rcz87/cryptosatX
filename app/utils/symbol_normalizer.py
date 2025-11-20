"""
Universal Symbol Normalization Utility

Provides automatic symbol conversion for all API providers:
- CoinGlass: BTC -> BTCUSDT
- LunarCrush: BTC -> BTC (uppercase)
- CoinAPI: BTC -> BINANCE_SPOT_BTC_USDT
- Binance: BTC -> BTCUSDT
- OKX: BTC -> BTC-USDT-SWAP
- CoinGecko: BTC -> bitcoin

Supported Input Formats:
- Short symbols: BTC, SOL, ETH
- Full symbols: BTCUSDT, SOLUSDT
- CoinGecko IDs: bitcoin, solana, ethereum
- Exchange formats: BTC-USDT-SWAP (OKX), BINANCE_SPOT_BTC_USDT (CoinAPI)

Quote Currency: USDT only (hardcoded). All symbols are normalized to USDT pairs.
For USD, USDC, or other quote currencies, manual symbol formatting is required.

Created: November 2025
"""

from typing import Dict, Optional
from enum import Enum


class Provider(str, Enum):
    """Supported API providers"""
    COINGLASS = "coinglass"
    LUNARCRUSH = "lunarcrush"
    COINAPI = "coinapi"
    BINANCE = "binance"
    OKX = "okx"
    COINGECKO = "coingecko"


# Symbol to CoinGecko ID mapping (most popular coins)
SYMBOL_TO_COINGECKO_ID: Dict[str, str] = {
    # Top 20 by market cap
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "USDC": "usd-coin",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "SHIB": "shiba-inu",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "XLM": "stellar",
    "BCH": "bitcoin-cash",
    
    # DeFi & Layer 2
    "ARB": "arbitrum",
    "OP": "optimism",
    "IMX": "immutable-x",
    "APT": "aptos",
    "SUI": "sui",
    "INJ": "injective-protocol",
    "SEI": "sei-network",
    "FTM": "fantom",
    "NEAR": "near",
    "AAVE": "aave",
    "MKR": "maker",
    "SNX": "havven",
    
    # Memecoins & Gaming
    "PEPE": "pepetoken",
    "FLOKI": "floki",
    "BONK": "bonk",
    "WIF": "dogwifcoin",
    "MEME": "memecoin-2",
    "GALA": "gala",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "AXS": "axie-infinity",
    
    # AI & Infrastructure
    "FET": "fetch-ai",
    "RNDR": "render-token",
    "GRT": "the-graph",
    "THETA": "theta-token",
    "FIL": "filecoin",
    "AR": "arweave",
    
    # Exchanges & Platforms
    "OKB": "okb",
    "CAKE": "pancakeswap-token",
    "CRO": "crypto-com-chain",
    "KCS": "kucoin-shares",
    
    # Stablecoins
    "DAI": "dai",
    "TUSD": "true-usd",
    "BUSD": "binance-usd",
    "USDD": "usdd",
}


# CoinGecko ID to Symbol (reverse mapping)
COINGECKO_ID_TO_SYMBOL: Dict[str, str] = {v: k for k, v in SYMBOL_TO_COINGECKO_ID.items()}


class SymbolNormalizer:
    """Universal symbol normalization for all providers"""
    
    def __init__(self):
        self.symbol_map = SYMBOL_TO_COINGECKO_ID
        self.reverse_map = COINGECKO_ID_TO_SYMBOL
    
    def normalize(self, symbol: str, provider: Provider, exchange: str = "BINANCE") -> str:
        """
        Normalize symbol for specific provider
        
        Args:
            symbol: Input symbol (e.g., "BTC", "BTCUSDT", "bitcoin")
            provider: Target provider (coinglass, lunarcrush, coinapi, etc.)
            exchange: Exchange name for CoinAPI (default: BINANCE)
            
        Returns:
            Normalized symbol for the provider
            
        Examples:
            normalize("BTC", Provider.COINGLASS) -> "BTCUSDT"
            normalize("BTC", Provider.OKX) -> "BTC-USDT-SWAP"
            normalize("BTC", Provider.COINGECKO) -> "bitcoin"
            normalize("BTCUSDT", Provider.LUNARCRUSH) -> "BTC"
        """
        if provider == Provider.COINGLASS:
            return self._normalize_coinglass(symbol)
        elif provider == Provider.LUNARCRUSH:
            return self._normalize_lunarcrush(symbol)
        elif provider == Provider.COINAPI:
            return self._normalize_coinapi(symbol, exchange)
        elif provider == Provider.BINANCE:
            return self._normalize_binance(symbol)
        elif provider == Provider.OKX:
            return self._normalize_okx(symbol)
        elif provider == Provider.COINGECKO:
            return self._normalize_coingecko(symbol)
        else:
            return symbol.upper()
    
    def _normalize_coinglass(self, symbol: str) -> str:
        """
        Normalize for CoinGlass API
        Format: BTCUSDT, SOLUSDT (uppercase, no separator)
        
        Examples:
            BTC -> BTCUSDT
            SOL -> SOLUSDT
            BTCUSDT -> BTCUSDT (unchanged)
        """
        symbol = symbol.upper().strip()
        
        # Already formatted
        if symbol.endswith("USDT") or symbol.endswith("USD"):
            return symbol
        
        # Auto-append USDT
        return f"{symbol}USDT"
    
    def _normalize_lunarcrush(self, symbol: str) -> str:
        """
        Normalize for LunarCrush API
        Format: BTC, ETH, SOL (uppercase, short form)
        
        Examples:
            BTC -> BTC
            BTCUSDT -> BTC (strip USDT)
            bitcoin -> BTC (convert from CoinGecko ID)
        """
        symbol = symbol.upper().strip()
        
        # Strip USDT/USD suffix if present
        if symbol.endswith("USDT"):
            symbol = symbol[:-4]
        elif symbol.endswith("USD"):
            symbol = symbol[:-3]
        
        # Try to convert from CoinGecko ID (if lowercase detected)
        if symbol.lower() in self.reverse_map:
            return self.reverse_map[symbol.lower()]
        
        return symbol
    
    def _normalize_coinapi(self, symbol: str, exchange: str = "BINANCE") -> str:
        """
        Normalize for CoinAPI
        Format: BINANCE_SPOT_BTC_USDT (exchange_spot_symbol_quote)
        
        Examples:
            BTC -> BINANCE_SPOT_BTC_USDT
            BTC, exchange=OKX -> OKX_SPOT_BTC_USDT
            BTCUSDT -> BINANCE_SPOT_BTC_USDT
        """
        symbol = symbol.upper().strip()
        exchange = exchange.upper().strip()
        
        # If already in CoinAPI format, return as-is
        if "_SPOT_" in symbol:
            return symbol
        
        # Strip USDT/USD if present (we'll add it back)
        if symbol.endswith("USDT"):
            symbol = symbol[:-4]
        elif symbol.endswith("USD"):
            symbol = symbol[:-3]
        
        return f"{exchange}_SPOT_{symbol}_USDT"
    
    def _normalize_binance(self, symbol: str) -> str:
        """
        Normalize for Binance Futures API
        Format: BTCUSDT, SOLUSDT (uppercase, no separator)
        
        Examples:
            BTC -> BTCUSDT
            SOL -> SOLUSDT
            BTCUSDT -> BTCUSDT (unchanged)
        """
        symbol = symbol.upper().strip()
        
        # Already formatted
        if symbol.endswith("USDT") or symbol.endswith("USD"):
            return symbol
        
        # Auto-append USDT
        return f"{symbol}USDT"
    
    def _normalize_okx(self, symbol: str, perpetual: bool = True) -> str:
        """
        Normalize for OKX API
        Format: BTC-USDT-SWAP (perpetual) or BTC-USDT (spot)
        
        Examples:
            BTC -> BTC-USDT-SWAP
            BTC, perpetual=False -> BTC-USDT
            BTC-USDT-SWAP -> BTC-USDT-SWAP (unchanged)
        """
        symbol = symbol.upper().strip()
        
        # Already in OKX perpetual format
        if symbol.endswith("-USDT-SWAP"):
            return symbol
        
        # Already in OKX spot format
        if symbol.endswith("-USDT"):
            return f"{symbol}-SWAP" if perpetual else symbol
        
        # Strip USDT if no dash (e.g., BTCUSDT -> BTC)
        if "USDT" in symbol and "-" not in symbol:
            symbol = symbol.replace("USDT", "")
        
        # Build OKX format
        if perpetual:
            return f"{symbol}-USDT-SWAP"
        else:
            return f"{symbol}-USDT"
    
    def _normalize_coingecko(self, symbol: str) -> str:
        """
        Normalize for CoinGecko API
        Format: bitcoin, ethereum, solana (lowercase full name)
        
        Examples:
            BTC -> bitcoin
            SOL -> solana
            bitcoin -> bitcoin (unchanged)
            BTCUSDT -> bitcoin (strip USDT, then lookup)
        """
        symbol = symbol.strip()
        
        # Already in CoinGecko ID format (lowercase)
        if symbol.islower() and symbol in self.reverse_map.values():
            return symbol
        
        # Convert to uppercase for lookup
        symbol_upper = symbol.upper()
        
        # Strip USDT/USD suffix
        if symbol_upper.endswith("USDT"):
            symbol_upper = symbol_upper[:-4]
        elif symbol_upper.endswith("USD"):
            symbol_upper = symbol_upper[:-3]
        
        # Lookup in mapping
        if symbol_upper in self.symbol_map:
            return self.symbol_map[symbol_upper]
        
        # Fallback: return lowercase version
        return symbol.lower()
    
    def detect_provider_from_format(self, symbol: str) -> Optional[Provider]:
        """
        Auto-detect which provider format is being used
        
        Returns:
            Provider enum or None if cannot detect
        """
        symbol = symbol.strip()
        
        if "_SPOT_" in symbol.upper():
            return Provider.COINAPI
        elif symbol.endswith("-USDT-SWAP") or symbol.endswith("-USDT"):
            return Provider.OKX
        elif symbol.islower() and "-" not in symbol:
            return Provider.COINGECKO
        elif symbol.upper().endswith("USDT") or symbol.upper().endswith("USD"):
            # Could be Binance, CoinGlass, or already normalized
            return Provider.BINANCE  # Default assumption
        else:
            # Short form like "BTC", "ETH"
            return Provider.LUNARCRUSH  # Default for short symbols
    
    def add_custom_mapping(self, symbol: str, coingecko_id: str):
        """
        Add custom symbol mapping for coins not in default dictionary
        
        Args:
            symbol: Short symbol (e.g., "XYZ")
            coingecko_id: CoinGecko ID (e.g., "xyz-token")
        """
        self.symbol_map[symbol.upper()] = coingecko_id.lower()
        self.reverse_map[coingecko_id.lower()] = symbol.upper()


# Global instance
symbol_normalizer = SymbolNormalizer()


# Convenience functions
def normalize_symbol(symbol: str, provider: str, exchange: str = "BINANCE") -> str:
    """
    Normalize symbol for any provider
    
    Args:
        symbol: Input symbol
        provider: Provider name (coinglass, lunarcrush, coinapi, binance, okx, coingecko)
        exchange: Exchange for CoinAPI (default: BINANCE)
    
    Returns:
        Normalized symbol
    """
    provider_enum = Provider(provider.lower())
    return symbol_normalizer.normalize(symbol, provider_enum, exchange)


def get_base_symbol(symbol: str) -> str:
    """
    Extract base symbol from any format
    
    Examples:
        BTCUSDT -> BTC
        BTC-USDT-SWAP -> BTC
        BINANCE_SPOT_BTC_USDT -> BTC
        bitcoin -> BTC
    """
    symbol_original = symbol.strip()
    
    # Check CoinGecko format FIRST (before uppercasing!)
    if symbol_original.islower() and symbol_original in COINGECKO_ID_TO_SYMBOL:
        return COINGECKO_ID_TO_SYMBOL[symbol_original]
    
    # Now uppercase for other formats
    symbol = symbol_original.upper()
    
    # CoinAPI format
    if "_SPOT_" in symbol:
        parts = symbol.split("_")
        return parts[2] if len(parts) > 2 else symbol
    
    # OKX format
    if "-USDT-SWAP" in symbol:
        return symbol.split("-")[0]
    elif "-USDT" in symbol:
        return symbol.split("-")[0]
    
    # Binance/CoinGlass format
    if symbol.endswith("USDT"):
        return symbol[:-4]
    elif symbol.endswith("USD"):
        return symbol[:-3]
    
    # Already base symbol
    return symbol


def get_coingecko_id(symbol: str) -> Optional[str]:
    """
    Convert symbol to CoinGecko ID
    
    Args:
        symbol: Symbol in any format (BTC, BTCUSDT, bitcoin, etc.)
        
    Returns:
        CoinGecko ID (e.g., 'bitcoin') or None if not found
        
    Examples:
        BTC -> bitcoin
        BTCUSDT -> bitcoin
        bitcoin -> bitcoin
        ETH -> ethereum
    """
    # If already a CoinGecko ID (lowercase), return as-is
    if symbol.islower() and symbol in COINGECKO_ID_TO_SYMBOL:
        return symbol
    
    # Get base symbol first (handles BTCUSDT, BTC-USDT-SWAP, etc.)
    base = get_base_symbol(symbol)
    
    # Look up in mapping
    return SYMBOL_TO_COINGECKO_ID.get(base, None)
