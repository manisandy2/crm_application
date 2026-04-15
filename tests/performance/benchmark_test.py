"""
Pytest-based Performance Benchmarks for /filter-datas Endpoint

This script uses pytest-benchmark to measure and compare performance
across different scenarios.

Usage:
    # Run all benchmarks
    pytest benchmark_test.py -v --benchmark-only

    # Run with detailed statistics
    pytest benchmark_test.py -v --benchmark-only --benchmark-verbose

    # Generate HTML report
    pytest benchmark_test.py --benchmark-only --benchmark-autosave \
           --benchmark-save-data --benchmark-html=reports/benchmark_report.html

    # Compare with previous runs
    pytest benchmark_test.py --benchmark-compare
"""

import pytest
import requests
from config import (
    API_BASE_URL,
    get_auth_headers,
    TestDataGenerator,
    PerformanceThresholds
)


class TestFilterDataPerformance:
    """Performance benchmarks for /filter-datas endpoint"""
    
    @pytest.fixture(scope="class")
    def api_headers(self):
        """Get authentication headers"""
        return get_auth_headers()
    
    @pytest.fixture(scope="class")
    def generator(self):
        """Get test data generator"""
        return TestDataGenerator()
    
    # ==================== Simple Queries ====================
    
    def test_simple_pagination_p1_l10(self, benchmark, api_headers):
        """Benchmark: Simple query - Page 1, Limit 10"""
        params = {"page": 1, "limit": 10}
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
        if result.status_code == 200:
            data = result.json()
            assert "data" in data
            assert len(data["data"]) <= 10
    
    def test_simple_pagination_p1_l50(self, benchmark, api_headers):
        """Benchmark: Simple query - Page 1, Limit 50"""
        params = {"page": 1, "limit": 50}
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    def test_simple_pagination_p1_l100(self, benchmark, api_headers):
        """Benchmark: Simple query - Page 1, Limit 100 (max)"""
        params = {"page": 1, "limit": 100}
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    # ==================== Date Range Queries ====================
    
    def test_date_range_7_days(self, benchmark, api_headers, generator):
        """Benchmark: Date range query - Last 7 days"""
        start_date, end_date = generator.generate_date_range(days_back=7)
        params = {
            "page": 1,
            "limit": 20,
            "startDate": start_date,
            "endDate": end_date
        }
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    def test_date_range_30_days(self, benchmark, api_headers, generator):
        """Benchmark: Date range query - Last 30 days"""
        start_date, end_date = generator.generate_date_range(days_back=30)
        params = {
            "page": 1,
            "limit": 20,
            "startDate": start_date,
            "endDate": end_date
        }
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    # ==================== Complex Queries ====================
    
    def test_complex_multiple_filters(self, benchmark, api_headers, generator):
        """Benchmark: Complex query with multiple filters"""
        start_date, end_date = generator.generate_date_range(days_back=15)
        params = {
            "page": 1,
            "limit": 20,
            "startDate": start_date,
            "endDate": end_date,
            "productName": generator.PRODUCT_NAMES[0],
            "branchName": generator.BRANCH_NAMES[0]
        }
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    def test_complex_with_warehouse_codes(self, benchmark, api_headers, generator):
        """Benchmark: Complex query with warehouse codes"""
        start_date, end_date = generator.generate_date_range(days_back=15)
        warehouse_codes = generator.generate_warehouse_codes(3)
        
        params = {
            "page": 1,
            "limit": 20,
            "startDate": start_date,
            "endDate": end_date,
        }
        
        # Add multiple warehouse_code params
        url = f"{API_BASE_URL}/filter-datas"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        query_string += "&" + "&".join([f"warehouse_code={code}" for code in warehouse_codes])
        full_url = f"{url}?{query_string}"
        
        result = benchmark(
            requests.get,
            full_url,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    # ==================== Pagination Performance ====================
    
    def test_pagination_page_10(self, benchmark, api_headers):
        """Benchmark: Deep pagination - Page 10"""
        params = {"page": 10, "limit": 20}
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]
    
    def test_pagination_page_50(self, benchmark, api_headers):
        """Benchmark: Very deep pagination - Page 50"""
        params = {"page": 50, "limit": 20}
        
        result = benchmark(
            requests.get,
            f"{API_BASE_URL}/filter-datas",
            params=params,
            headers=api_headers,
            timeout=30
        )
        
        assert result.status_code in [200, 404]


# ==================== Performance Validation Tests ====================

class TestPerformanceThresholds:
    """Validate that performance meets defined thresholds"""
    
    @pytest.fixture(scope="class")
    def api_headers(self):
        return get_auth_headers()
    
    def test_response_time_under_threshold(self, api_headers):
        """Validate response time is under P95 threshold"""
        import time
        
        params = {"page": 1, "limit": 20}
        
        # Make 10 requests and check average
        response_times = []
        for _ in range(10):
            start = time.time()
            response = requests.get(
                f"{API_BASE_URL}/filter-datas",
                params=params,
                headers=api_headers,
                timeout=30
            )
            elapsed = time.time() - start
            response_times.append(elapsed)
            
            assert response.status_code in [200, 404]
        
        avg_time = sum(response_times) / len(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        print(f"\nAverage response time: {avg_time:.2f}s")
        print(f"P95 response time: {p95_time:.2f}s")
        print(f"Threshold: {PerformanceThresholds.RESPONSE_TIME_P95}s")
        
        assert p95_time < PerformanceThresholds.RESPONSE_TIME_P95, \
            f"P95 response time {p95_time:.2f}s exceeds threshold {PerformanceThresholds.RESPONSE_TIME_P95}s"
    
    def test_concurrent_requests_success_rate(self, api_headers):
        """Validate success rate under concurrent load"""
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(
                    f"{API_BASE_URL}/filter-datas",
                    params={"page": 1, "limit": 10},
                    headers=api_headers,
                    timeout=30
                )
                return response.status_code in [200, 404]
            except:
                return False
        
        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: make_request(), range(20)))
        
        success_count = sum(results)
        success_rate = (success_count / len(results)) * 100
        
        print(f"\nSuccess rate: {success_rate:.1f}% ({success_count}/{len(results)})")
        
        assert success_rate >= (100 - PerformanceThresholds.MAX_ERROR_RATE), \
            f"Success rate {success_rate:.1f}% is below threshold"
