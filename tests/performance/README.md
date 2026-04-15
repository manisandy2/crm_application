# Performance Testing Suite

Comprehensive performance testing tools for the `/filter-datas` endpoint.

## 📋 Overview

This suite includes:
- **Locust Load Testing** - Simulate concurrent users with realistic traffic patterns
- **Pytest Benchmarks** - Measure and compare performance across scenarios
- **Stress Testing** - Identify breaking points under extreme load
- **Real-time Monitoring** - Track performance metrics live
- **Automated Test Runner** - Run all tests with a single command

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/mac-1/Desktop/CRM_Application
pip install -r requirements-test.txt
```

### 2. Set JWT Token

```bash
export JWT_TOKEN="your-jwt-token-here"
export API_BASE_URL="http://localhost:8000"  # Optional, defaults to localhost
```

### 3. Run Tests

```bash
cd tests/performance
chmod +x run_tests.sh

# Interactive mode
./run_tests.sh

# Or run specific profile
./run_tests.sh quick      # Quick smoke test (~2 min)
./run_tests.sh standard   # Full test suite (~10 min)
./run_tests.sh stress     # Stress test (~15 min)
./run_tests.sh all        # Run everything
```

## 📊 Test Types

### 1. Locust Load Testing

Simulates multiple concurrent users making requests with various filter combinations.

**Usage:**
```bash
# Web UI mode (recommended for first-time users)
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 in browser

# Headless mode with HTML report
locust -f locustfile.py --host=http://localhost:8000 \
       --users 20 --spawn-rate 2 --run-time 5m --headless \
       --html reports/load_test.html
```

**Test Scenarios:**
- Simple pagination (50% of traffic)
- Date range filtering (30% of traffic)
- Complex multi-filter queries (20% of traffic)
- Large page size requests (10% of traffic)

### 2. Pytest Benchmarks

Measures response times for specific scenarios and validates against thresholds.

**Usage:**
```bash
# Run all benchmarks
pytest benchmark_test.py -v --benchmark-only

# Generate HTML report
pytest benchmark_test.py --benchmark-only \
       --benchmark-html=reports/benchmark.html

# Compare with previous runs
pytest benchmark_test.py --benchmark-compare
```

**Test Coverage:**
- Simple pagination (various page sizes)
- Date range queries (7 days, 30 days)
- Complex multi-filter queries
- Deep pagination performance
- Threshold validation

### 3. Stress Testing

Tests endpoint under extreme concurrent load using asyncio.

**Usage:**
```bash
# 100 concurrent users for 2 minutes
python stress_test.py --users 100 --duration 120

# With gradual ramp-up
python stress_test.py --users 200 --duration 180 --ramp-up 30
```

**Metrics Tracked:**
- Total requests and throughput
- Success/failure rates
- Response time percentiles (P50, P95, P99)
- Error breakdown

### 4. Real-time Monitoring

Monitors endpoint performance in real-time with live dashboard.

**Usage:**
```bash
# Dashboard mode (default)
python monitor.py --duration 300 --interval 1

# Log mode
python monitor.py --duration 600 --interval 0.5 --output log
```

**Dashboard Shows:**
- Rolling window metrics (last 60 requests)
- Response time statistics
- Throughput and error rates
- Health status indicator

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# API Configuration
API_BASE_URL = "http://localhost:8000"
JWT_TOKEN = "your-token"

# Performance Thresholds
RESPONSE_TIME_P95 = 3.0  # seconds
MAX_ERROR_RATE = 1.0     # percentage
MIN_THROUGHPUT = 10      # requests/second

# Test Profiles
QUICK = {"users": 5, "duration": "1m"}
STANDARD = {"users": 20, "duration": "5m"}
STRESS = {"users": 100, "duration": "10m"}
```

## 📈 Understanding Results

### Response Time Thresholds

| Metric | Target | Status |
|--------|--------|--------|
| P50 | < 1.0s | ✓ Good |
| P95 | < 3.0s | ⚠ Acceptable |
| P99 | < 5.0s | ⚠ Acceptable |

### Error Rate

- **< 1%** - ✓ Healthy
- **1-5%** - ⚠ Warning
- **> 5%** - ✗ Critical

### Throughput

- **> 10 req/s** - ✓ Meets minimum
- **> 50 req/s** - ✓ Good
- **> 100 req/s** - ✓ Excellent

## 📁 Reports

All reports are saved to `tests/performance/reports/`:

- **HTML Reports** - `*_load_test_*.html`, `benchmark_*.html`
- **JSON Metrics** - `*_metrics_*.json`, `stress_test_*.json`
- **Consolidated Report** - `consolidated_report_*.txt`

## 🔧 Troubleshooting

### JWT Token Issues

```bash
# Verify token is set
echo $JWT_TOKEN

# Test authentication manually
curl -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:8000/filter-datas?page=1&limit=10
```

### Connection Errors

- Ensure API server is running
- Check `API_BASE_URL` is correct
- Verify firewall/network settings

### Performance Issues

If tests are failing thresholds:
1. Check database query performance
2. Review pagination implementation
3. Monitor server resources (CPU, memory)
4. Consider adding caching
5. Optimize Iceberg scan filters

## 💡 Best Practices

1. **Start Small** - Run quick tests first before stress testing
2. **Use Test Environment** - Don't run stress tests on production
3. **Monitor Resources** - Watch server CPU/memory during tests
4. **Baseline First** - Establish baseline metrics before optimization
5. **Iterate** - Test → Optimize → Test again

## 📚 Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Performance Testing Best Practices](https://www.nginx.com/blog/performance-testing-best-practices/)

## 🐛 Common Issues

**Issue:** `ModuleNotFoundError: No module named 'locust'`  
**Solution:** Run `pip install -r requirements-test.txt`

**Issue:** `ValueError: JWT_TOKEN not set`  
**Solution:** Export JWT token: `export JWT_TOKEN="your-token"`

**Issue:** Tests timing out  
**Solution:** Increase timeout in `config.py` or check API server status

**Issue:** Permission denied on `run_tests.sh`  
**Solution:** Make executable: `chmod +x run_tests.sh`
