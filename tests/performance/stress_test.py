"""
Stress Testing Script for /filter-datas Endpoint

This script performs stress testing using asyncio to simulate
extreme concurrent load and identify breaking points.

Usage:
    python stress_test.py --users 100 --duration 60
    python stress_test.py --users 200 --duration 120 --ramp-up 30
"""

import asyncio
import aiohttp
import time
import argparse
import statistics
from datetime import datetime
from typing import List, Dict
from config import (
    API_BASE_URL,
    get_auth_headers,
    TestDataGenerator,
    PerformanceThresholds,
    get_report_filename
)
import json


class StressTest:
    """Stress testing orchestrator"""
    
    def __init__(self, num_users: int, duration: int, ramp_up: int = 0):
        self.num_users = num_users
        self.duration = duration
        self.ramp_up = ramp_up
        self.generator = TestDataGenerator()
        self.headers = get_auth_headers()
        self.results: List[Dict] = []
        self.start_time = None
        self.errors = []
    
    async def make_request(self, session: aiohttp.ClientSession, user_id: int):
        """Make a single API request"""
        # Generate random filter params
        complexity = ["simple", "medium", "complex"][user_id % 3]
        params = self.generator.generate_filter_params(complexity)
        
        request_start = time.time()
        
        try:
            async with session.get(
                f"{API_BASE_URL}/filter-datas",
                params=params,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_time = time.time() - request_start
                status = response.status
                
                # Try to read response
                try:
                    data = await response.json()
                except:
                    data = None
                
                self.results.append({
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "response_time": response_time,
                    "status_code": status,
                    "success": status in [200, 404],
                    "complexity": complexity
                })
                
                return status in [200, 404]
        
        except asyncio.TimeoutError:
            response_time = time.time() - request_start
            self.errors.append({
                "user_id": user_id,
                "error": "Timeout",
                "timestamp": datetime.now().isoformat()
            })
            self.results.append({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time,
                "status_code": 0,
                "success": False,
                "complexity": complexity,
                "error": "Timeout"
            })
            return False
        
        except Exception as e:
            response_time = time.time() - request_start
            self.errors.append({
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.results.append({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time,
                "status_code": 0,
                "success": False,
                "complexity": complexity,
                "error": str(e)
            })
            return False
    
    async def user_simulation(self, session: aiohttp.ClientSession, user_id: int):
        """Simulate a single user making continuous requests"""
        end_time = self.start_time + self.duration
        
        # Ramp-up delay
        if self.ramp_up > 0:
            delay = (self.ramp_up / self.num_users) * user_id
            await asyncio.sleep(delay)
        
        request_count = 0
        while time.time() < end_time:
            await self.make_request(session, user_id)
            request_count += 1
            
            # Small delay between requests (0.5-2 seconds)
            await asyncio.sleep(0.5 + (user_id % 3) * 0.5)
        
        return request_count
    
    async def run(self):
        """Run the stress test"""
        print(f"\n{'='*70}")
        print(f"STRESS TEST CONFIGURATION")
        print(f"{'='*70}")
        print(f"Concurrent Users:  {self.num_users}")
        print(f"Duration:          {self.duration}s")
        print(f"Ramp-up:           {self.ramp_up}s")
        print(f"Target URL:        {API_BASE_URL}/filter-datas")
        print(f"{'='*70}\n")
        
        self.start_time = time.time()
        
        # Create session with connection pooling
        connector = aiohttp.TCPConnector(limit=self.num_users)
        async with aiohttp.ClientSession(connector=connector) as session:
            print(f"Starting stress test at {datetime.now().strftime('%H:%M:%S')}...")
            
            # Create tasks for all users
            tasks = [
                self.user_simulation(session, user_id)
                for user_id in range(self.num_users)
            ]
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        
        actual_duration = time.time() - self.start_time
        
        # Generate report
        self.generate_report(actual_duration)
    
    def generate_report(self, actual_duration: float):
        """Generate and display test report"""
        if not self.results:
            print("No results to report")
            return
        
        # Calculate metrics
        total_requests = len(self.results)
        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]
        
        success_count = len(successful)
        failure_count = len(failed)
        error_rate = (failure_count / total_requests * 100) if total_requests > 0 else 0
        
        # Response time statistics
        response_times = [r["response_time"] for r in successful]
        
        if response_times:
            avg_response = statistics.mean(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
            median_response = statistics.median(response_times)
            
            sorted_times = sorted(response_times)
            p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0
            p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0
        else:
            avg_response = min_response = max_response = median_response = p95 = p99 = 0
        
        # Throughput
        throughput = total_requests / actual_duration if actual_duration > 0 else 0
        
        # Print report
        print(f"\n{'='*70}")
        print(f"STRESS TEST RESULTS")
        print(f"{'='*70}")
        print(f"Test Duration:         {actual_duration:.2f}s")
        print(f"Total Requests:        {total_requests}")
        print(f"Successful:            {success_count} ({success_count/total_requests*100:.1f}%)")
        print(f"Failed:                {failure_count} ({error_rate:.1f}%)")
        print(f"Throughput:            {throughput:.2f} req/s")
        print(f"\nResponse Times (seconds):")
        print(f"  Average:             {avg_response:.3f}")
        print(f"  Median:              {median_response:.3f}")
        print(f"  Min:                 {min_response:.3f}")
        print(f"  Max:                 {max_response:.3f}")
        print(f"  P95:                 {p95:.3f}")
        print(f"  P99:                 {p99:.3f}")
        
        # Threshold validation
        print(f"\nThreshold Validation:")
        p95_pass = p95 < PerformanceThresholds.RESPONSE_TIME_P95
        error_pass = error_rate < PerformanceThresholds.MAX_ERROR_RATE
        throughput_pass = throughput > PerformanceThresholds.MIN_THROUGHPUT
        
        print(f"  P95 < {PerformanceThresholds.RESPONSE_TIME_P95}s:        {'✓ PASS' if p95_pass else '✗ FAIL'}")
        print(f"  Error Rate < {PerformanceThresholds.MAX_ERROR_RATE}%:      {'✓ PASS' if error_pass else '✗ FAIL'}")
        print(f"  Throughput > {PerformanceThresholds.MIN_THROUGHPUT} req/s: {'✓ PASS' if throughput_pass else '✗ FAIL'}")
        
        # Error breakdown
        if self.errors:
            print(f"\nTop Errors:")
            error_types = {}
            for err in self.errors[:10]:
                error_msg = err.get("error", "Unknown")
                error_types[error_msg] = error_types.get(error_msg, 0) + 1
            
            for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error_msg}: {count}")
        
        print(f"{'='*70}\n")
        
        # Save detailed report
        report_data = {
            "configuration": {
                "users": self.num_users,
                "duration": self.duration,
                "ramp_up": self.ramp_up,
                "actual_duration": actual_duration
            },
            "summary": {
                "total_requests": total_requests,
                "successful": success_count,
                "failed": failure_count,
                "error_rate": error_rate,
                "throughput": throughput,
                "avg_response_time": avg_response,
                "median_response_time": median_response,
                "min_response_time": min_response,
                "max_response_time": max_response,
                "p95": p95,
                "p99": p99
            },
            "threshold_validation": {
                "p95_pass": p95_pass,
                "error_rate_pass": error_pass,
                "throughput_pass": throughput_pass
            },
            "detailed_results": self.results,
            "errors": self.errors
        }
        
        report_file = get_report_filename("stress_test", "json")
        try:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"Failed to save report: {e}")


def main():
    parser = argparse.ArgumentParser(description="Stress test for /filter-datas endpoint")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--ramp-up", type=int, default=0, help="Ramp-up time in seconds")
    
    args = parser.parse_args()
    
    test = StressTest(
        num_users=args.users,
        duration=args.duration,
        ramp_up=args.ramp_up
    )
    
    asyncio.run(test.run())


if __name__ == "__main__":
    main()
