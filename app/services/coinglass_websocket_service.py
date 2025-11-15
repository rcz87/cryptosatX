"""
Coinglass WebSocket Service - Real-time Liquidation Streaming!
Provides live liquidation data across all exchanges.
"""

import asyncio
import json
import os
from typing import Optional, Callable
from app.utils.logger import logger
import websockets
from websockets.client import WebSocketClientProtocol


class CoinglassWebSocketService:
    """
    Service for real-time Coinglass WebSocket connections.
    Streams live liquidation data across exchanges.
    """
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY", "")
        self.base_url = "wss://open-ws.coinglass.com/ws-api"
        self.ws: Optional[WebSocketClientProtocol] = None
        self.ping_interval = 20
        self.reconnect_interval = 5
        self.is_connected = False
        self.subscribed_channels = set()
    
    def get_connection_url(self) -> str:
        """Get WebSocket connection URL with API key."""
        return f"{self.base_url}?cg-api-key={self.api_key}"
    
    async def connect(self) -> WebSocketClientProtocol:
        """Establish WebSocket connection to Coinglass."""
        try:
            self.ws = await websockets.connect(self.get_connection_url())
            self.is_connected = True
            logger.info(f"✅ Connected to Coinglass WebSocket")
            return self.ws
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            raise
    
    async def subscribe(self, channels: list[str]) -> None:
        """
        Subscribe to WebSocket channels.
        
        Available channels:
        - liquidationOrders: Real-time liquidation data
        """
        if not self.ws or not self.is_connected:
            raise Exception("WebSocket not connected")
        
        subscribe_msg = {
            "method": "subscribe",
            "channels": channels
        }
        
        await self.ws.send(json.dumps(subscribe_msg))
        self.subscribed_channels.update(channels)
        logger.info(f"📡 Subscribed to channels: {channels}")
    
    async def unsubscribe(self, channels: list[str]) -> None:
        """Unsubscribe from WebSocket channels."""
        if not self.ws or not self.is_connected:
            raise Exception("WebSocket not connected")
        
        unsubscribe_msg = {
            "method": "unsubscribe",
            "channels": channels
        }
        
        await self.ws.send(json.dumps(unsubscribe_msg))
        self.subscribed_channels.difference_update(channels)
        logger.info(f"🔕 Unsubscribed from channels: {channels}")
    
    async def send_ping(self) -> None:
        """Send ping to keep connection alive."""
        if self.ws and self.is_connected:
            try:
                await self.ws.send("ping")
            except Exception as e:
                logger.warning(f"⚠️ Ping failed: {e}")
                self.is_connected = False
    
    async def keepalive(self) -> None:
        """Background task to keep connection alive with ping/pong."""
        while self.is_connected:
            await asyncio.sleep(self.ping_interval)
            await self.send_ping()
    
    async def listen(self, message_handler: Callable) -> None:
        """
        Listen for incoming WebSocket messages.
        
        Args:
            message_handler: Async function to handle received messages
        """
        if not self.ws or not self.is_connected:
            raise Exception("WebSocket not connected")
        
        try:
            async for message in self.ws:
                if message == "pong":
                    continue
                
                try:
                    data = json.loads(message)
                    await message_handler(data)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Failed to parse message: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"❌ Listen error: {e}")
            self.is_connected = False
    
    async def stream_liquidations(self, message_handler: Callable) -> None:
        """
        Stream real-time liquidations with auto-reconnect.
        
        Args:
            message_handler: Async function to handle liquidation data
        """
        while True:
            try:
                await self.connect()
                
                await self.subscribe(["liquidationOrders"])
                
                keepalive_task = asyncio.create_task(self.keepalive())
                listen_task = asyncio.create_task(self.listen(message_handler))
                
                await asyncio.gather(keepalive_task, listen_task)
                
            except Exception as e:
                logger.error(f"❌ Stream error: {e}")
                self.is_connected = False
                
                if self.ws:
                    await self.ws.close()
                
                logger.info(f"🔄 Reconnecting in {self.reconnect_interval}s...")
                await asyncio.sleep(self.reconnect_interval)
    
    async def close(self) -> None:
        """Close WebSocket connection."""
        self.is_connected = False
        
        if self.ws:
            try:
                await self.ws.close()
                logger.info("🔌 WebSocket connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing WebSocket: {e}")


async def process_liquidation(data: dict) -> None:
    """
    Example message handler for liquidation data.
    
    Liquidation data format:
    {
        "channel": "liquidationOrders",
        "data": [
            {
                "baseAsset": "BTC",
                "exName": "Binance",
                "price": 56738.00,
                "side": 2,  # 1=long liquidation, 2=short liquidation
                "symbol": "BTCUSDT",
                "time": 1725416318379,
                "volUsd": 3858.18
            }
        ]
    }
    """
    if data.get("channel") == "liquidationOrders":
        liquidations = data.get("data", [])
        
        for liq in liquidations:
            side = "LONG" if liq.get("side") == 1 else "SHORT"
            asset = liq.get("baseAsset", "")
            exchange = liq.get("exName", "")
            price = liq.get("price", 0)
            volume_usd = liq.get("volUsd", 0)
            
            logger.info(f"🔥 {side} Liquidation: {asset} on {exchange} | ${volume_usd:,.2f} @ ${price:,.2f}")
