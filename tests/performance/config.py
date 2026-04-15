"""
Performance Testing Configuration
Centralized configuration for all performance tests
"""
import os
from typing import Optional
from datetime import datetime, timedelta
import random

# ==================== API Configuration ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# ==================== Authentication ====================
# Set your JWT token here or via environment variable
JWT_TOKEN = os.getenv("JWT_TOKEN", "")

def get_auth_headers() -> dict:
    """Get authentication headers for API requests"""
    if not JWT_TOKEN:
        raise ValueError(
            "JWT_TOKEN not set. Please set it in environment or config.py"
        )
    return {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

# ==================== Test Data Generators ====================
class TestDataGenerator:
    """Generate realistic test data for performance testing"""
    
    PRODUCT_NAMES = [
        "iPhone 15 Pro", "Samsung Galaxy S24", "OnePlus 12",
        "Google Pixel 8", "Xiaomi 14", "Vivo X100"
    ]
    
    BRANCH_NAMES = [
        "Mumbai Central", "Delhi NCR", "Bangalore HSR",
        "Chennai T Nagar", "Kolkata Park Street", "Pune Koregaon"
    ]
    
    WAREHOUSE_CODES = ["WH001", "WH002", "WH003", "WH004", "WH005"]
    
    @staticmethod
    def generate_date_range(days_back: int = 30) -> tuple[str, str]:
        """Generate a random date range within the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=random.randint(1, days_back))
        return (
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
    
    @staticmethod
    def generate_filter_params(complexity: str = "simple") -> dict:
        """
        Generate filter parameters for testing
        
        Args:
            complexity: 'simple', 'medium', or 'complex'
        """
        params = {
            "page": random.randint(1, 5),
            "limit": random.choice([10, 20, 50, 100])
        }
        
        if complexity in ["medium", "complex"]:
            # Add date range
            start_date, end_date = TestDataGenerator.generate_date_range()
            params["startDate"] = start_date
            params["endDate"] = end_date
        
        if complexity == "complex":
            # Add multiple filters
            if random.random() > 0.5:
                params["productName"] = random.choice(TestDataGenerator.PRODUCT_NAMES)
            if random.random() > 0.5:
                params["branchName"] = random.choice(TestDataGenerator.BRANCH_NAMES)
        
        return params
    
    @staticmethod
    def generate_warehouse_codes(count: Optional[int] = None) -> list[str]:
        """Generate random warehouse codes"""
        if count is None:
            count = random.randint(1, 3)
        return random.sample(TestDataGenerator.WAREHOUSE_CODES, min(count, len(TestDataGenerator.WAREHOUSE_CODES)))

# ==================== Performance Test Profiles ====================
class TestProfile:
    """Predefined test profiles for different scenarios"""
    
    # Quick smoke test
    QUICK = {
        "users": 5,
        "spawn_rate": 1,
        "duration": "1m",
        "description": "Quick smoke test with low load"
    }
    
    # Standard load test
    STANDARD = {
        "users": 20,
        "spawn_rate": 2,
        "duration": "5m",
        "description": "Standard load test with moderate concurrent users"
    }
    
    # Stress test
    STRESS = {
        "users": 100,
        "spawn_rate": 10,
        "duration": "10m",
        "description": "Stress test with high concurrent load"
    }
    
    # Spike test
    SPIKE = {
        "users": 200,
        "spawn_rate": 50,
        "duration": "3m",
        "description": "Spike test with sudden load increase"
    }

# ==================== Performance Thresholds ====================
class PerformanceThresholds:
    """Expected performance thresholds"""
    
    # Response time thresholds (in seconds)
    RESPONSE_TIME_P50 = 1.0  # 50th percentile
    RESPONSE_TIME_P95 = 3.0  # 95th percentile
    RESPONSE_TIME_P99 = 5.0  # 99th percentile
    
    # Throughput (requests per second)
    MIN_THROUGHPUT = 10
    
    # Error rate (percentage)
    MAX_ERROR_RATE = 1.0
    
    # Memory usage (MB)
    MAX_MEMORY_MB = 512

# ==================== Report Configuration ====================
REPORT_DIR = "tests/performance/reports"
REPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

def get_report_filename(test_name: str, extension: str = "html") -> str:
    """Generate timestamped report filename"""
    timestamp = datetime.now().strftime(REPORT_TIMESTAMP_FORMAT)
    return f"{REPORT_DIR}/{test_name}_{timestamp}.{extension}"
