#!/usr/bin/env python3
"""
Data Validation Test - Validates schema compliance and data accuracy
Tests critical endpoints for required fields and data types
"""

import asyncio
import httpx
import json
from typing import Dict, List
from datetime import datetime

BASE_URL = "http://localhost:8000"

class DataValidator:
    def __init__(self):
        self.results = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "validation_details": []
        }
    
    async def validate_endpoint(self, name: str, url: str, required_fields: List[str], data_path: List[str] = None) -> Dict:
        """
        Validate endpoint response schema
        
        Args:
            name: Endpoint name
            url: Full URL
            required_fields: List of required field names
            data_path: Path to data in response (e.g., ['data', 'items'])
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return {
                        "name": name,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }
                
                data = response.json()
                
                # Navigate to data if path specified
                target_data = data
                if data_path:
                    for key in data_path:
                        if isinstance(target_data, dict):
                            target_data = target_data.get(key, {})
                        else:
                            return {
                                "name": name,
                                "success": False,
                                "error": f"Invalid data path at: {key}"
                            }
                
                # Handle both dict and list responses
                if isinstance(target_data, list):
                    if len(target_data) == 0:
                        return {
                            "name": name,
                            "success": False,
                            "error": "Empty data array"
                        }
                    target_data = target_data[0]  # Validate first item
                
                # Check required fields
                missing_fields = []
                for field in required_fields:
                    if field not in target_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    return {
                        "name": name,
                        "success": False,
                        "error": f"Missing fields: {missing_fields}",
                        "found_fields": list(target_data.keys())[:10]
                    }
                
                # Validation passed
                return {
                    "name": name,
                    "success": True,
                    "fields_validated": required_fields,
                    "additional_fields": [k for k in target_data.keys() if k not in required_fields][:5]
                }
        
        except Exception as e:
            return {
                "name": name,
                "success": False,
                "error": str(e)[:100]
            }
    
    async def run_validations(self):
        """Run all data validations"""
        
        print("=" * 80)
        print("🔍 DATA VALIDATION TEST - Schema & Required Fields")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Define critical endpoint validations
        validations = [
            # Market Data
            {
                "name": "Market Data - All Coins",
                "url": f"{BASE_URL}/coinglass/markets",
                "data_path": ["data"],
                "required_fields": ["symbol", "current_price", "market_cap_usd", "open_interest_usd"]
            },
            
            # Liquidations
            {
                "name": "Liquidations - History",
                "url": f"{BASE_URL}/coinglass/liquidation/history",
                "data_path": ["data", "dataMap", "BTCUSDT"],
                "required_fields": ["createTime", "longLiquidationUsd", "shortLiquidationUsd"]
            },
            
            # Funding Rates
            {
                "name": "Funding Rate - History",
                "url": f"{BASE_URL}/coinglass/funding-rate/history",
                "data_path": ["data", "dataMap", "BTCUSDT"],
                "required_fields": ["rate", "time"]
            },
            
            # Open Interest
            {
                "name": "Open Interest - History",
                "url": f"{BASE_URL}/coinglass/open-interest/history",
                "data_path": ["data", "dataMap", "BTCUSDT"],
                "required_fields": ["createTime", "h", "openInterest"]
            },
            
            # Long/Short Ratios
            {
                "name": "Long/Short - Account Ratio",
                "url": f"{BASE_URL}/coinglass/top-long-short-account-ratio/history",
                "data_path": ["data", "dataMap", "BTCUSDT"],
                "required_fields": ["longAccount", "shortAccount", "time"]
            },
            
            # Taker Volume
            {
                "name": "Taker Volume",
                "url": f"{BASE_URL}/coinglass/volume/taker-buy-sell",
                "data_path": ["data"],
                "required_fields": ["symbol", "buyRatio", "sellRatio"]
            },
            
            # Orderbook
            {
                "name": "Orderbook - Whale Walls",
                "url": f"{BASE_URL}/coinglass/orderbook/whale-walls",
                "data_path": ["data"],
                "required_fields": ["symbol", "price", "size"]
            },
            
            # Hyperliquid
            {
                "name": "Hyperliquid - Whale Alerts",
                "url": f"{BASE_URL}/coinglass/hyperliquid/whale-alerts",
                "data_path": ["data"],
                "required_fields": ["symbol", "side", "size", "price", "timestamp"]
            },
            
            # Technical Indicators
            {
                "name": "Indicators - RSI List",
                "url": f"{BASE_URL}/coinglass/indicators/rsi-list",
                "data_path": ["data"],
                "required_fields": ["symbol", "rsi"]
            },
            
            {
                "name": "Indicators - Fear & Greed",
                "url": f"{BASE_URL}/coinglass/indicators/fear-greed",
                "data_path": ["data"],
                "required_fields": ["value", "classification", "timestamp"]
            },
            
            # Options
            {
                "name": "Options - Open Interest",
                "url": f"{BASE_URL}/coinglass/options/open-interest",
                "data_path": ["data"],
                "required_fields": ["symbol", "openInterest", "timestamp"]
            },
            
            # Utility
            {
                "name": "Supported Coins",
                "url": f"{BASE_URL}/coinglass/supported-coins",
                "data_path": ["data"],
                "required_fields": ["symbol"]
            },
        ]
        
        print(f"📊 Validating {len(validations)} critical endpoints...\n")
        
        # Run validations in batches
        batch_size = 5
        for i in range(0, len(validations), batch_size):
            batch = validations[i:i+batch_size]
            
            tasks = [
                self.validate_endpoint(
                    v["name"],
                    v["url"],
                    v["required_fields"],
                    v.get("data_path")
                ) for v in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            
            for result in batch_results:
                self.results["total_validations"] += 1
                self.results["validation_details"].append(result)
                
                if result["success"]:
                    self.results["passed"] += 1
                    print(f"✅ {result['name'][:60]:<60} | {len(result['fields_validated'])} fields OK")
                else:
                    self.results["failed"] += 1
                    error = result.get('error', 'Unknown')[:50]
                    print(f"❌ {result['name'][:60]:<60} | {error}")
            
            await asyncio.sleep(1)
        
        print("\n" + "=" * 80)
        self.generate_report()
    
    def generate_report(self):
        """Generate validation report"""
        
        print("\n📋 DATA VALIDATION REPORT")
        print("=" * 80)
        
        success_rate = (self.results["passed"] / self.results["total_validations"] * 100) if self.results["total_validations"] > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Validations: {self.results['total_validations']}")
        print(f"  ✅ Passed: {self.results['passed']}")
        print(f"  ❌ Failed: {self.results['failed']}")
        print(f"  📈 Success Rate: {success_rate:.1f}%")
        
        # Failed validations
        if self.results["failed"] > 0:
            print(f"\n❌ FAILED VALIDATIONS:")
            failed = [v for v in self.results["validation_details"] if not v["success"]]
            for f in failed[:10]:
                print(f"  • {f['name']}")
                print(f"    Error: {f.get('error', 'Unknown')}")
                if 'found_fields' in f:
                    print(f"    Found: {f['found_fields']}")
        
        # Assessment
        print(f"\n💡 ASSESSMENT:")
        if success_rate >= 90:
            print("  ✅ EXCELLENT - Data schemas validated")
        elif success_rate >= 70:
            print("  ⚠️  GOOD - Minor schema issues")
        else:
            print("  🚨 CRITICAL - Schema validation failures")
        
        # Save report
        with open("data_validation_report.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": self.results["total_validations"],
                    "passed": self.results["passed"],
                    "failed": self.results["failed"],
                    "success_rate": success_rate
                },
                "details": self.results["validation_details"]
            }, f, indent=2)
        
        print(f"\n📄 Report saved: data_validation_report.json")
        print("=" * 80)

async def main():
    validator = DataValidator()
    await validator.run_validations()

if __name__ == "__main__":
    asyncio.run(main())
