"""
Locust Load Testing Script for /filter-datas Endpoint

This script simulates multiple concurrent users making requests to the
filter-datas endpoint with various filter combinations.

Usage:
    # Web UI mode (recommended)
    locust -f locustfile.py --host=http://localhost:8000
    # Then open http://localhost:8089

    # Headless mode
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 20 --spawn-rate 2 --run-time 5m --headless

    # With HTML report
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 20 --spawn-rate 2 --run-time 5m --headless \
           --html reports/load_test_report.html
"""

from locust import HttpUser, task, between, events
from config import (
    TestDataGenerator,
    get_auth_headers,
    PerformanceThresholds,
    get_report_filename
)
import random
import json
import time
from datetime import datetime

# Global metrics storage
request_metrics = []


class FilterDataUser(HttpUser):
    """
    Simulates a user making requests to the /filter-datas endpoint
    """
    
    # Wait between 1-3 seconds between tasks (simulates user think time)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.headers = get_auth_headers()
        self.generator = TestDataGenerator()
    
    @task(5)
    def filter_simple_query(self):
        """
        Simple query with just pagination (most common use case)
        Weight: 5 (50% of requests)
        """
        params = {
            "page": random.randint(1, 10),
            "limit": random.choice([10, 20, 50])
        }
        
        with self.client.get(
            "/filter-datas",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/filter-datas [simple]"
        ) as response:
            self._validate_response(response, "simple")
    
    @task(3)
    def filter_with_date_range(self):
        """
        Query with date range filter
        Weight: 3 (30% of requests)
        """
        params = self.generator.generate_filter_params(complexity="medium")
        
        with self.client.get(
            "/filter-datas",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/filter-datas [date_range]"
        ) as response:
            self._validate_response(response, "date_range")
    
    @task(2)
    def filter_complex_query(self):
        """
        Complex query with multiple filters
        Weight: 2 (20% of requests)
        """
        params = self.generator.generate_filter_params(complexity="complex")
        warehouse_codes = self.generator.generate_warehouse_codes(2)
        
        # Add warehouse codes as multiple query params
        for code in warehouse_codes:
            params.setdefault("warehouse_code", []).append(code)
        
        with self.client.get(
            "/filter-datas",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/filter-datas [complex]"
        ) as response:
            self._validate_response(response, "complex")
    
    @task(1)
    def filter_large_page_size(self):
        """
        Query with maximum page size (stress test)
        Weight: 1 (10% of requests)
        """
        params = {
            "page": 1,
            "limit": 100  # Maximum allowed
        }
        
        with self.client.get(
            "/filter-datas",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/filter-datas [large_page]"
        ) as response:
            self._validate_response(response, "large_page")
    
    def _validate_response(self, response, query_type: str):
        """Validate API response and mark success/failure"""
        try:
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["status", "page", "limit", "total_records", "data"]
                if all(field in data for field in required_fields):
                    # Check response time against threshold
                    if response.elapsed.total_seconds() > PerformanceThresholds.RESPONSE_TIME_P95:
                        response.failure(
                            f"Response time {response.elapsed.total_seconds():.2f}s "
                            f"exceeds threshold {PerformanceThresholds.RESPONSE_TIME_P95}s"
                        )
                    else:
                        response.success()
                else:
                    response.failure(f"Missing required fields in response")
            
            elif response.status_code == 404:
                # 404 is acceptable (no data found)
                response.success()
            
            elif response.status_code == 401:
                response.failure("Authentication failed - check JWT token")
            
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
        
        except json.JSONDecodeError:
            response.failure("Invalid JSON response")
        except Exception as e:
            response.failure(f"Validation error: {str(e)}")


# ==================== Event Handlers ====================

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Capture request metrics for custom reporting"""
    request_metrics.append({
        "timestamp": datetime.now().isoformat(),
        "request_type": request_type,
        "name": name,
        "response_time": response_time,
        "response_length": response_length,
        "success": exception is None,
        "exception": str(exception) if exception else None
    })


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate custom report when test stops"""
    if not request_metrics:
        return
    
    # Calculate statistics
    response_times = [m["response_time"] for m in request_metrics if m["success"]]
    total_requests = len(request_metrics)
    successful_requests = len([m for m in request_metrics if m["success"]])
    failed_requests = total_requests - successful_requests
    error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
    else:
        avg_response_time = min_response_time = max_response_time = 0
        p50 = p95 = p99 = 0
    
    # Print summary
    print("\n" + "="*70)
    print("PERFORMANCE TEST SUMMARY")
    print("="*70)
    print(f"Total Requests:        {total_requests}")
    print(f"Successful:            {successful_requests}")
    print(f"Failed:                {failed_requests}")
    print(f"Error Rate:            {error_rate:.2f}%")
    print(f"\nResponse Times (ms):")
    print(f"  Average:             {avg_response_time:.2f}")
    print(f"  Min:                 {min_response_time:.2f}")
    print(f"  Max:                 {max_response_time:.2f}")
    print(f"  P50:                 {p50:.2f}")
    print(f"  P95:                 {p95:.2f}")
    print(f"  P99:                 {p99:.2f}")
    print(f"\nThreshold Validation:")
    print(f"  P95 < {PerformanceThresholds.RESPONSE_TIME_P95*1000}ms:  {'✓ PASS' if p95 < PerformanceThresholds.RESPONSE_TIME_P95*1000 else '✗ FAIL'}")
    print(f"  Error Rate < {PerformanceThresholds.MAX_ERROR_RATE}%:    {'✓ PASS' if error_rate < PerformanceThresholds.MAX_ERROR_RATE else '✗ FAIL'}")
    print("="*70 + "\n")
    
    # Save metrics to JSON
    report_file = get_report_filename("locust_metrics", "json")
    try:
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "error_rate": error_rate,
                    "avg_response_time": avg_response_time,
                    "min_response_time": min_response_time,
                    "max_response_time": max_response_time,
                    "p50": p50,
                    "p95": p95,
                    "p99": p99
                },
                "metrics": request_metrics
            }, f, indent=2)
        print(f"Detailed metrics saved to: {report_file}")
    except Exception as e:
        print(f"Failed to save metrics: {e}")
