#!/bin/bash
#
# Test runner script for Nexus Analyzer backend
#
# Usage:
#   ./scripts/run_tests.sh              # Run all tests
#   ./scripts/run_tests.sh --fast       # Run only fast tests (no slow marker)
#   ./scripts/run_tests.sh --coverage   # Run with coverage report
#   ./scripts/run_tests.sh --auth       # Run only auth tests
#   ./scripts/run_tests.sh --help       # Show help

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default options
PYTEST_ARGS=""
SHOW_COVERAGE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            echo -e "${BLUE}Running fast tests only (excluding slow tests)${NC}"
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
            shift
            ;;
        --coverage)
            echo -e "${BLUE}Running with coverage report${NC}"
            SHOW_COVERAGE=true
            shift
            ;;
        --auth)
            echo -e "${BLUE}Running auth tests only${NC}"
            PYTEST_ARGS="$PYTEST_ARGS -m auth"
            shift
            ;;
        --api)
            echo -e "${BLUE}Running API tests only${NC}"
            PYTEST_ARGS="$PYTEST_ARGS -m api"
            shift
            ;;
        --unit)
            echo -e "${BLUE}Running unit tests only${NC}"
            PYTEST_ARGS="$PYTEST_ARGS -m unit"
            shift
            ;;
        --integration)
            echo -e "${BLUE}Running integration tests only${NC}"
            PYTEST_ARGS="$PYTEST_ARGS -m integration"
            shift
            ;;
        --security)
            echo -e "${BLUE}Running security tests only${NC}"
            PYTEST_ARGS="$PYTEST_ARGS -m security"
            shift
            ;;
        --help)
            echo "Nexus Analyzer Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fast         Run only fast tests (exclude slow tests)"
            echo "  --coverage     Generate coverage report"
            echo "  --auth         Run only authentication tests"
            echo "  --api          Run only API tests"
            echo "  --unit         Run only unit tests"
            echo "  --integration  Run only integration tests"
            echo "  --security     Run only security tests"
            echo "  --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run all tests"
            echo "  $0 --fast --coverage  # Run fast tests with coverage"
            echo "  $0 --auth             # Run only auth tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Nexus Analyzer Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Navigate to backend directory if not already there
if [ ! -f "pytest.ini" ]; then
    if [ -d "backend" ]; then
        cd backend
    else
        echo -e "${RED}Error: Could not find backend directory${NC}"
        exit 1
    fi
fi

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo ""

if [ "$SHOW_COVERAGE" = true ]; then
    pytest $PYTEST_ARGS --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml
    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Tests passed!${NC}"
        echo ""
        echo -e "${YELLOW}Coverage report generated:${NC}"
        echo "  HTML: htmlcov/index.html"
        echo "  XML:  coverage.xml"
        echo ""
        echo -e "${BLUE}To view HTML report:${NC}"
        echo "  open htmlcov/index.html      # macOS"
        echo "  xdg-open htmlcov/index.html  # Linux"
        echo "  start htmlcov/index.html     # Windows"
    else
        echo -e "${RED}✗ Tests failed${NC}"
        exit $EXIT_CODE
    fi
else
    pytest $PYTEST_ARGS
    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        exit $EXIT_CODE
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Test run complete${NC}"
echo -e "${GREEN}========================================${NC}"
