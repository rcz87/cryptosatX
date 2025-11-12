#!/usr/bin/env python3
"""
WebSocket Stability Test
Tests Coinglass WebSocket real-time liquidation streaming
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

WS_URL = "ws://localhost:8000/coinglass/ws/liquidations"

class WebSocketStabilityTester:
    def __init__(self):
        self.stats = {
            "messages_received": 0,
            "errors": 0,
            "disconnections": 0,
            "reconnections": 0,
            "start_time": None,
            "message_timestamps": [],
            "data_samples": []
        }
    
    async def test_connection(self, duration_seconds=30):
        """Test WebSocket connection for specified duration"""
        
        print("=" * 80)
        print("🔌 WEBSOCKET STABILITY TEST")
        print("=" * 80)
        print(f"URL: {WS_URL}")
        print(f"Duration: {duration_seconds}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.stats["start_time"] = time.time()
        end_time = self.stats["start_time"] + duration_seconds
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                print("✅ WebSocket connected successfully\n")
                print("📊 Receiving real-time liquidation data...")
                print("-" * 80)
                
                while time.time() < end_time:
                    try:
                        # Set timeout for receiving messages
                        message = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=5.0
                        )
                        
                        self.stats["messages_received"] += 1
                        self.stats["message_timestamps"].append(time.time())
                        
                        try:
                            data = json.loads(message)
                            
                            # Store first 5 samples
                            if len(self.stats["data_samples"]) < 5:
                                self.stats["data_samples"].append(data)
                            
                            # Display sample data
                            if self.stats["messages_received"] <= 3:
                                print(f"Message #{self.stats['messages_received']}:")
                                
                                # Safely extract message type
                                if 'status' in data:
                                    print(f"  Type: connection_status")
                                    print(f"  Status: {data.get('status')}")
                                elif 'channel' in data:
                                    print(f"  Type: data_update")
                                    print(f"  Channel: {data.get('channel')}")
                                    # Handle data field (can be list or dict)
                                    if 'data' in data:
                                        data_field = data['data']
                                        if isinstance(data_field, list):
                                            print(f"  Data count: {len(data_field)} items")
                                            if len(data_field) > 0 and isinstance(data_field[0], dict):
                                                print(f"  First item keys: {list(data_field[0].keys())}")
                                        elif isinstance(data_field, dict):
                                            print(f"  Data keys: {list(data_field.keys())}")
                                else:
                                    print(f"  Type: unknown")
                                print()
                            elif self.stats["messages_received"] % 10 == 0:
                                # Progress indicator every 10 messages
                                elapsed = time.time() - self.stats["start_time"]
                                rate = self.stats["messages_received"] / elapsed
                                print(f"  📈 Messages: {self.stats['messages_received']} | Rate: {rate:.2f} msg/s")
                        
                        except json.JSONDecodeError:
                            print(f"  ⚠️ Non-JSON message: {message[:100]}")
                    
                    except asyncio.TimeoutError:
                        print("  ⏱️  No message received in 5s (this may be normal)")
                        continue
                    
                    except Exception as e:
                        self.stats["errors"] += 1
                        print(f"  ❌ Error receiving message: {str(e)[:100]}")
                
                print("\n" + "-" * 80)
                print("✅ Test duration completed")
        
        except websockets.exceptions.WebSocketException as e:
            self.stats["disconnections"] += 1
            print(f"\n❌ WebSocket connection error: {str(e)[:100]}")
        
        except Exception as e:
            self.stats["errors"] += 1
            print(f"\n❌ Unexpected error: {str(e)[:100]}")
        
        finally:
            self.generate_report()
    
    def generate_report(self):
        """Generate WebSocket stability report"""
        
        print("\n" + "=" * 80)
        print("📋 WEBSOCKET STABILITY REPORT")
        print("=" * 80)
        
        elapsed = time.time() - self.stats["start_time"]
        
        print(f"\n📊 STATISTICS:")
        print(f"  Total Runtime: {elapsed:.1f}s")
        print(f"  Messages Received: {self.stats['messages_received']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Disconnections: {self.stats['disconnections']}")
        
        if self.stats["messages_received"] > 0:
            rate = self.stats["messages_received"] / elapsed
            print(f"  Message Rate: {rate:.2f} msg/s")
            
            # Calculate message timing stats
            if len(self.stats["message_timestamps"]) > 1:
                intervals = [
                    self.stats["message_timestamps"][i] - self.stats["message_timestamps"][i-1]
                    for i in range(1, len(self.stats["message_timestamps"]))
                ]
                avg_interval = sum(intervals) / len(intervals)
                print(f"  Avg Message Interval: {avg_interval:.3f}s")
        
        # Data quality
        if self.stats["data_samples"]:
            print(f"\n📦 DATA QUALITY:")
            print(f"  Sample Messages Collected: {len(self.stats['data_samples'])}")
            
            # Analyze first message
            first_msg = self.stats['data_samples'][0]
            if 'status' in first_msg:
                print(f"  First Message: Connection status")
            elif 'channel' in first_msg:
                print(f"  First Message: Data update (channel: {first_msg.get('channel')})")
                if 'data' in first_msg:
                    data_field = first_msg['data']
                    if isinstance(data_field, list):
                        print(f"  Data Structure: List with {len(data_field)} items")
                    elif isinstance(data_field, dict):
                        print(f"  Data Structure: Dict with keys {list(data_field.keys())}")
        
        # Assessment
        print(f"\n💡 ASSESSMENT:")
        
        if self.stats["messages_received"] == 0:
            print("  🚨 CRITICAL - No messages received")
            print("  ⚠️  Check if WebSocket endpoint is properly configured")
        elif self.stats["errors"] > self.stats["messages_received"] * 0.1:
            print("  ⚠️  WARNING - High error rate (>10%)")
        elif self.stats["disconnections"] > 0:
            print("  ⚠️  WARNING - Connection stability issues detected")
        else:
            print("  ✅ EXCELLENT - WebSocket connection stable and reliable")
        
        # Recommendations
        if self.stats["messages_received"] > 0:
            if rate < 0.1:
                print("  💡 Message rate is low - this may be normal during quiet trading periods")
            elif rate > 10:
                print("  💡 High message rate - consider implementing message throttling")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "runtime_seconds": elapsed,
                "messages_received": self.stats["messages_received"],
                "errors": self.stats["errors"],
                "disconnections": self.stats["disconnections"],
                "message_rate": self.stats["messages_received"] / elapsed if elapsed > 0 else 0
            },
            "data_samples": self.stats["data_samples"][:3]  # Save first 3 samples
        }
        
        with open("websocket_stability_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved: websocket_stability_report.json")
        print("=" * 80)

async def main():
    tester = WebSocketStabilityTester()
    # Test for 30 seconds
    await tester.test_connection(duration_seconds=30)

if __name__ == "__main__":
    asyncio.run(main())
