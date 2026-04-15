"""
Real-time Performance Monitoring Utility

This script monitors the /filter-datas endpoint in real-time,
tracking response times, throughput, and system metrics.

Usage:
    # Monitor for 5 minutes with 1 request per second
    python monitor.py --duration 300 --interval 1

    # Monitor with custom parameters
    python monitor.py --duration 600 --interval 0.5 --output dashboard
"""

import requests
import time
import argparse
from datetime import datetime
from collections import deque
from typing import Deque, Dict, List
import statistics
import json
from config import (
    API_BASE_URL,
    get_auth_headers,
    TestDataGenerator,
    get_report_filename
)


class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self, interval: float = 1.0, window_size: int = 60):
        self.interval = interval
        self.window_size = window_size
        self.headers = get_auth_headers()
        self.generator = TestDataGenerator()
        
        # Rolling windows for metrics
        self.response_times: Deque[float] = deque(maxlen=window_size)
        self.timestamps: Deque[datetime] = deque(maxlen=window_size)
        self.statuses: Deque[int] = deque(maxlen=window_size)
        
        # Cumulative metrics
        self.total_requests = 0
        self.total_errors = 0
        self.all_response_times: List[float] = []
    
    def make_request(self) -> Dict:
        """Make a single monitoring request"""
        params = {"page": 1, "limit": 10}
        
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/filter-datas",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            response_time = time.time() - start_time
            status_code = response.status_code
            success = status_code in [200, 404]
            
            return {
                "timestamp": datetime.now(),
                "response_time": response_time,
                "status_code": status_code,
                "success": success
            }
        
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "timestamp": datetime.now(),
                "response_time": response_time,
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
    
    def update_metrics(self, result: Dict):
        """Update rolling metrics"""
        self.timestamps.append(result["timestamp"])
        self.response_times.append(result["response_time"])
        self.statuses.append(result["status_code"])
        self.all_response_times.append(result["response_time"])
        
        self.total_requests += 1
        if not result["success"]:
            self.total_errors += 1
    
    def get_current_metrics(self) -> Dict:
        """Calculate current metrics from rolling window"""
        if not self.response_times:
            return {}
        
        # Response time stats
        avg_response = statistics.mean(self.response_times)
        min_response = min(self.response_times)
        max_response = max(self.response_times)
        
        # Calculate throughput (requests per second)
        if len(self.timestamps) > 1:
            time_span = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
            throughput = len(self.timestamps) / time_span if time_span > 0 else 0
        else:
            throughput = 0
        
        # Error rate
        errors_in_window = sum(1 for s in self.statuses if s not in [200, 404])
        error_rate = (errors_in_window / len(self.statuses) * 100) if self.statuses else 0
        
        # Overall error rate
        overall_error_rate = (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "window_avg_response": avg_response,
            "window_min_response": min_response,
            "window_max_response": max_response,
            "window_throughput": throughput,
            "window_error_rate": error_rate,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "overall_error_rate": overall_error_rate
        }
    
    def display_dashboard(self, metrics: Dict):
        """Display real-time dashboard"""
        # Clear screen (works on Unix-like systems)
        print("\033[2J\033[H", end="")
        
        print(f"{'='*70}")
        print(f"PERFORMANCE MONITORING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Endpoint: {API_BASE_URL}/filter-datas")
        print(f"Window Size: {self.window_size} requests")
        print(f"{'='*70}")
        
        if metrics:
            print(f"\n📊 CURRENT WINDOW METRICS (Last {self.window_size} requests)")
            print(f"  Response Time (avg): {metrics['window_avg_response']:.3f}s")
            print(f"  Response Time (min): {metrics['window_min_response']:.3f}s")
            print(f"  Response Time (max): {metrics['window_max_response']:.3f}s")
            print(f"  Throughput:          {metrics['window_throughput']:.2f} req/s")
            print(f"  Error Rate:          {metrics['window_error_rate']:.1f}%")
            
            print(f"\n📈 CUMULATIVE METRICS")
            print(f"  Total Requests:      {metrics['total_requests']}")
            print(f"  Total Errors:        {metrics['total_errors']}")
            print(f"  Overall Error Rate:  {metrics['overall_error_rate']:.1f}%")
            
            # Visual indicator
            print(f"\n🚦 STATUS")
            if metrics['window_avg_response'] < 1.0 and metrics['window_error_rate'] < 1.0:
                print(f"  ✓ HEALTHY - Performance is good")
            elif metrics['window_avg_response'] < 3.0 and metrics['window_error_rate'] < 5.0:
                print(f"  ⚠ WARNING - Performance degraded")
            else:
                print(f"  ✗ CRITICAL - Performance issues detected")
        
        print(f"\n{'='*70}")
        print(f"Press Ctrl+C to stop monitoring")
        print(f"{'='*70}")
    
    def run(self, duration: int, output_mode: str = "dashboard"):
        """Run monitoring for specified duration"""
        print(f"Starting performance monitoring...")
        print(f"Duration: {duration}s | Interval: {self.interval}s")
        print(f"Output: {output_mode}\n")
        
        start_time = time.time()
        end_time = start_time + duration
        
        try:
            while time.time() < end_time:
                # Make request
                result = self.make_request()
                self.update_metrics(result)
                
                # Display metrics
                if output_mode == "dashboard":
                    metrics = self.get_current_metrics()
                    self.display_dashboard(metrics)
                elif output_mode == "log":
                    print(f"[{result['timestamp'].strftime('%H:%M:%S')}] "
                          f"Status: {result['status_code']} | "
                          f"Time: {result['response_time']:.3f}s")
                
                # Wait for next interval
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate final monitoring report"""
        if not self.all_response_times:
            print("No data collected")
            return
        
        # Calculate final statistics
        avg_response = statistics.mean(self.all_response_times)
        median_response = statistics.median(self.all_response_times)
        min_response = min(self.all_response_times)
        max_response = max(self.all_response_times)
        
        sorted_times = sorted(self.all_response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        error_rate = (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"MONITORING SUMMARY")
        print(f"{'='*70}")
        print(f"Total Requests:        {self.total_requests}")
        print(f"Total Errors:          {self.total_errors}")
        print(f"Error Rate:            {error_rate:.1f}%")
        print(f"\nResponse Times (seconds):")
        print(f"  Average:             {avg_response:.3f}")
        print(f"  Median:              {median_response:.3f}")
        print(f"  Min:                 {min_response:.3f}")
        print(f"  Max:                 {max_response:.3f}")
        print(f"  P95:                 {p95:.3f}")
        print(f"  P99:                 {p99:.3f}")
        print(f"{'='*70}\n")
        
        # Save report
        report_data = {
            "summary": {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate": error_rate,
                "avg_response_time": avg_response,
                "median_response_time": median_response,
                "min_response_time": min_response,
                "max_response_time": max_response,
                "p95": p95,
                "p99": p99
            },
            "all_response_times": self.all_response_times
        }
        
        report_file = get_report_filename("monitor", "json")
        try:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"Report saved to: {report_file}")
        except Exception as e:
            print(f"Failed to save report: {e}")


def main():
    parser = argparse.ArgumentParser(description="Monitor /filter-datas endpoint performance")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=float, default=1.0, help="Request interval in seconds")
    parser.add_argument("--window", type=int, default=60, help="Rolling window size")
    parser.add_argument("--output", choices=["dashboard", "log"], default="dashboard", help="Output mode")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(
        interval=args.interval,
        window_size=args.window
    )
    
    monitor.run(duration=args.duration, output_mode=args.output)


if __name__ == "__main__":
    main()
