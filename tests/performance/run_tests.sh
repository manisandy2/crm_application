#!/bin/bash

# Performance Testing Automation Script
# This script runs various performance tests and generates consolidated reports

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$SCRIPT_DIR/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Ensure reports directory exists
mkdir -p "$REPORT_DIR"

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print section header
print_header() {
    echo ""
    print_message "$BLUE" "========================================================================"
    print_message "$BLUE" "$1"
    print_message "$BLUE" "========================================================================"
    echo ""
}

# Check if JWT token is set
check_jwt_token() {
    if [ -z "$JWT_TOKEN" ]; then
        print_message "$RED" "ERROR: JWT_TOKEN environment variable is not set"
        print_message "$YELLOW" "Please set it using: export JWT_TOKEN='your-token-here'"
        exit 1
    fi
}

# Run quick tests (smoke test)
run_quick_tests() {
    print_header "Running Quick Performance Tests (Smoke Test)"
    
    # Quick benchmark
    print_message "$GREEN" "Running pytest benchmarks (quick)..."
    pytest benchmark_test.py::TestFilterDataPerformance::test_simple_pagination_p1_l10 \
           -v --benchmark-only --benchmark-autosave
    
    # Quick load test
    print_message "$GREEN" "Running Locust load test (5 users, 1 minute)..."
    locust -f locustfile.py --host="$API_BASE_URL" \
           --users 5 --spawn-rate 1 --run-time 1m --headless \
           --html "$REPORT_DIR/quick_load_test_${TIMESTAMP}.html"
    
    print_message "$GREEN" "✓ Quick tests completed"
}

# Run standard tests
run_standard_tests() {
    print_header "Running Standard Performance Tests"
    
    # Full benchmark suite
    print_message "$GREEN" "Running full pytest benchmark suite..."
    pytest benchmark_test.py -v --benchmark-only --benchmark-autosave \
           --benchmark-html="$REPORT_DIR/benchmark_${TIMESTAMP}.html"
    
    # Standard load test
    print_message "$GREEN" "Running Locust load test (20 users, 5 minutes)..."
    locust -f locustfile.py --host="$API_BASE_URL" \
           --users 20 --spawn-rate 2 --run-time 5m --headless \
           --html "$REPORT_DIR/standard_load_test_${TIMESTAMP}.html"
    
    # Performance threshold validation
    print_message "$GREEN" "Running performance threshold validation..."
    pytest benchmark_test.py::TestPerformanceThresholds -v
    
    print_message "$GREEN" "✓ Standard tests completed"
}

# Run stress tests
run_stress_tests() {
    print_header "Running Stress Tests"
    
    print_message "$YELLOW" "WARNING: Stress tests will put significant load on your system"
    print_message "$YELLOW" "Make sure you're running against a test environment"
    
    # Stress test with asyncio
    print_message "$GREEN" "Running async stress test (100 users, 2 minutes)..."
    python stress_test.py --users 100 --duration 120 --ramp-up 30
    
    # Heavy load test with Locust
    print_message "$GREEN" "Running Locust stress test (100 users, 10 minutes)..."
    locust -f locustfile.py --host="$API_BASE_URL" \
           --users 100 --spawn-rate 10 --run-time 10m --headless \
           --html "$REPORT_DIR/stress_test_${TIMESTAMP}.html"
    
    print_message "$GREEN" "✓ Stress tests completed"
}

# Run monitoring
run_monitoring() {
    print_header "Running Performance Monitoring"
    
    local duration=${1:-300}  # Default 5 minutes
    
    print_message "$GREEN" "Monitoring endpoint for ${duration} seconds..."
    python monitor.py --duration "$duration" --interval 1 --output dashboard
    
    print_message "$GREEN" "✓ Monitoring completed"
}

# Generate consolidated report
generate_report() {
    print_header "Generating Consolidated Report"
    
    local report_file="$REPORT_DIR/consolidated_report_${TIMESTAMP}.txt"
    
    {
        echo "========================================================================"
        echo "PERFORMANCE TEST CONSOLIDATED REPORT"
        echo "Generated: $(date)"
        echo "========================================================================"
        echo ""
        echo "Test Configuration:"
        echo "  API Base URL: $API_BASE_URL"
        echo "  Report Directory: $REPORT_DIR"
        echo ""
        echo "Generated Reports:"
        ls -lh "$REPORT_DIR"/*"${TIMESTAMP}"* 2>/dev/null || echo "  No reports found"
        echo ""
        echo "Latest JSON Metrics:"
        echo "========================================================================"
        
        # Find and display latest metrics
        latest_json=$(ls -t "$REPORT_DIR"/*.json 2>/dev/null | head -1)
        if [ -n "$latest_json" ]; then
            cat "$latest_json"
        else
            echo "No JSON metrics found"
        fi
    } > "$report_file"
    
    print_message "$GREEN" "✓ Consolidated report saved to: $report_file"
    cat "$report_file"
}

# Main menu
show_menu() {
    echo ""
    print_message "$BLUE" "Performance Testing Suite"
    echo "1) Quick Tests (Smoke Test - ~2 minutes)"
    echo "2) Standard Tests (Full Suite - ~10 minutes)"
    echo "3) Stress Tests (Heavy Load - ~15 minutes)"
    echo "4) Monitor (Real-time monitoring)"
    echo "5) Run All Tests"
    echo "6) Exit"
    echo ""
}

# Main execution
main() {
    cd "$SCRIPT_DIR"
    
    # Check prerequisites
    check_jwt_token
    
    # Set default API base URL if not set
    export API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
    
    print_header "Performance Testing Suite for /filter-datas Endpoint"
    print_message "$GREEN" "API Base URL: $API_BASE_URL"
    print_message "$GREEN" "Report Directory: $REPORT_DIR"
    
    # Check if profile argument is provided
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select option: " choice
            
            case $choice in
                1)
                    run_quick_tests
                    generate_report
                    ;;
                2)
                    run_standard_tests
                    generate_report
                    ;;
                3)
                    run_stress_tests
                    generate_report
                    ;;
                4)
                    read -p "Enter monitoring duration in seconds (default 300): " duration
                    duration=${duration:-300}
                    run_monitoring "$duration"
                    ;;
                5)
                    run_quick_tests
                    run_standard_tests
                    run_stress_tests
                    generate_report
                    ;;
                6)
                    print_message "$GREEN" "Exiting..."
                    exit 0
                    ;;
                *)
                    print_message "$RED" "Invalid option"
                    ;;
            esac
        done
    else
        # Command-line mode
        case $1 in
            quick)
                run_quick_tests
                generate_report
                ;;
            standard)
                run_standard_tests
                generate_report
                ;;
            stress)
                run_stress_tests
                generate_report
                ;;
            monitor)
                run_monitoring "${2:-300}"
                ;;
            all)
                run_quick_tests
                run_standard_tests
                run_stress_tests
                generate_report
                ;;
            *)
                print_message "$RED" "Invalid profile: $1"
                print_message "$YELLOW" "Usage: $0 [quick|standard|stress|monitor|all]"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
