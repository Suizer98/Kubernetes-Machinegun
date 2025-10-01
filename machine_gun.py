#!/usr/bin/env python3
"""
Kubernetes Machine Gun - Load Testing System
Simulates various attack patterns against FastAPI backend
"""

import asyncio
import aiohttp
import time
import random
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from faker import Faker

fake = Faker()

class MachineGun:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make a single HTTP request"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                content = await response.text()
                
                self.stats["total_requests"] += 1
                if response.status < 400:
                    self.stats["successful_requests"] += 1
                else:
                    self.stats["failed_requests"] += 1
                    self.stats["errors"].append({
                        "status": response.status,
                        "endpoint": endpoint,
                        "timestamp": datetime.now().isoformat()
                    })
                
                self.stats["response_times"].append(response_time)
                
                return {
                    "status": response.status,
                    "response_time": response_time,
                    "content": content
                }
        except Exception as e:
            response_time = time.time() - start_time
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            self.stats["errors"].append({
                "error": str(e),
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            })
            return {"error": str(e), "response_time": response_time}
    
    async def ddos_attack(self, duration: int = 60, rps: int = 1000):
        """Simulate DDoS attack with high RPS"""
        print(f"🚀 Starting DDoS attack: {rps} RPS for {duration}s")
        
        end_time = time.time() + duration
        tasks = []
        
        while time.time() < end_time:
            # Create burst of requests
            burst_tasks = []
            for _ in range(rps // 10):  # 10 requests per burst
                endpoint = random.choice([
                    "/cpu-intensive",
                    "/memory-intensive", 
                    "/database-heavy",
                    "/slow-endpoint",
                    "/error-prone"
                ])
                burst_tasks.append(self.make_request(endpoint))
            
            tasks.extend(burst_tasks)
            await asyncio.sleep(0.1)  # 100ms between bursts
        
        # Wait for all requests to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        self.print_stats()
    
    async def burst_attack(self, burst_size: int = 500, interval: int = 5, duration: int = 60):
        """Simulate burst traffic patterns"""
        print(f"💥 Starting burst attack: {burst_size} requests every {interval}s for {duration}s")
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            print(f"Firing burst of {burst_size} requests...")
            tasks = []
            
            for _ in range(burst_size):
                endpoint = random.choice([
                    "/cpu-intensive?n=100000",
                    "/memory-intensive?size_mb=50",
                    "/database-heavy?queries=50",
                    "/queue-task"
                ])
                
                if endpoint == "/queue-task":
                    data = {"task": f"burst_task_{int(time.time())}", "data": fake.text()}
                    tasks.append(self.make_request(endpoint, "POST", json=data))
                else:
                    tasks.append(self.make_request(endpoint))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(interval)
        
        self.print_stats()
    
    async def sustained_attack(self, rps: int = 100, duration: int = 300):
        """Sustained high load"""
        print(f"🔥 Starting sustained attack: {rps} RPS for {duration}s")
        
        end_time = time.time() + duration
        interval = 1.0 / rps
        
        while time.time() < end_time:
            start = time.time()
            
            endpoint = random.choice([
                "/cpu-intensive?n=500000",
                "/memory-intensive?size_mb=25",
                "/database-heavy?queries=25",
                "/slow-endpoint?delay=1.0"
            ])
            
            asyncio.create_task(self.make_request(endpoint))
            
            # Maintain RPS
            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            await asyncio.sleep(sleep_time)
        
        self.print_stats()
    
    async def random_attack(self, max_rps: int = 200, duration: int = 120):
        """Random unpredictable traffic"""
        print(f"🎲 Starting random attack: up to {max_rps} RPS for {duration}s")
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Random RPS between 0 and max_rps
            current_rps = random.randint(0, max_rps)
            
            if current_rps > 0:
                tasks = []
                for _ in range(current_rps):
                    endpoint = random.choice([
                        "/cpu-intensive",
                        "/memory-intensive",
                        "/database-heavy",
                        "/slow-endpoint",
                        "/error-prone",
                        "/queue-task",
                        "/metrics"
                    ])
                    
                    if endpoint == "/queue-task":
                        data = {"task": f"random_task_{int(time.time())}"}
                        tasks.append(self.make_request(endpoint, "POST", json=data))
                    else:
                        tasks.append(self.make_request(endpoint))
                
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Random interval between 0.1 and 2 seconds
            await asyncio.sleep(random.uniform(0.1, 2.0))
        
        self.print_stats()
    
    async def database_attack(self, duration: int = 180):
        """Database-specific stress test"""
        print(f"🗄️ Starting database attack for {duration}s")
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            tasks = []
            
            # Heavy database operations
            for _ in range(50):
                tasks.append(self.make_request("/database-heavy?queries=100"))
            
            # Queue operations
            for _ in range(20):
                data = {"task": f"db_task_{int(time.time())}", "queries": 50}
                tasks.append(self.make_request("/queue-task", "POST", json=data))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.5)
        
        self.print_stats()
    
    def print_stats(self):
        """Print attack statistics"""
        if not self.stats["response_times"]:
            print("No requests completed")
            return
        
        response_times = self.stats["response_times"]
        success_rate = (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
        
        print("\n" + "="*50)
        print("🎯 ATTACK STATISTICS")
        print("="*50)
        print(f"Total Requests: {self.stats['total_requests']}")
        print(f"Successful: {self.stats['successful_requests']} ({success_rate:.1f}%)")
        print(f"Failed: {self.stats['failed_requests']}")
        print(f"Average Response Time: {np.mean(response_times):.3f}s")
        print(f"Min Response Time: {np.min(response_times):.3f}s")
        print(f"Max Response Time: {np.max(response_times):.3f}s")
        print(f"95th Percentile: {np.percentile(response_times, 95):.3f}s")
        
        if self.stats["errors"]:
            print(f"\nRecent Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"][-5:]:  # Show last 5 errors
                print(f"  - {error}")

async def main():
    parser = argparse.ArgumentParser(description="Kubernetes Machine Gun")
    parser.add_argument("--attack", choices=["ddos", "burst", "sustained", "random", "database"], 
                       default="ddos", help="Attack type")
    parser.add_argument("--target", default="http://localhost:8000", help="Target URL")
    parser.add_argument("--duration", type=int, default=60, help="Attack duration in seconds")
    parser.add_argument("--rps", type=int, default=100, help="Requests per second")
    parser.add_argument("--burst-size", type=int, default=500, help="Burst size for burst attack")
    
    args = parser.parse_args()
    
    print(f"🔫 Kubernetes Machine Gun targeting {args.target}")
    print(f"Attack: {args.attack}, Duration: {args.duration}s")
    
    async with MachineGun(args.target) as gun:
        if args.attack == "ddos":
            await gun.ddos_attack(args.duration, args.rps)
        elif args.attack == "burst":
            await gun.burst_attack(args.burst_size, 5, args.duration)
        elif args.attack == "sustained":
            await gun.sustained_attack(args.rps, args.duration)
        elif args.attack == "random":
            await gun.random_attack(args.rps, args.duration)
        elif args.attack == "database":
            await gun.database_attack(args.duration)

if __name__ == "__main__":
    asyncio.run(main())
