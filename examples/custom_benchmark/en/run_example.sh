#!/bin/bash
#
# One-click runner for the custom benchmark example
#
# This script automatically:
# 1. Generates raw data
# 2. Prepares train/test datasets
# 3. Executes the benchmark test
#

set -e  # Exit on any error

# Colored output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Custom Benchmark Example - House Price Prediction       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

# Resolve script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Step 1/3: Generate raw data${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 prepare_example_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Data generation failed${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 2/3: Prepare dataset (train/test split)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd competitions/custom_house_price_prediction
python3 prepare.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Data preparation failed${NC}"
    exit 1
fi
cd "$SCRIPT_DIR"
echo ""

echo -e "${YELLOW}Step 3/3: Run benchmark test${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 custom_benchmark.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Benchmark run failed${NC}"
    exit 1
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   ✅ Done!                                               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Results saved to:${NC} test_results/"
echo ""
echo "Next:"
echo "  • Inspect submissions: ls -lh test_results/"
echo "  • Read the docs: cat README.md"
echo "  • Integrate: see the \"Framework Integration\" section in README.md"
echo ""
