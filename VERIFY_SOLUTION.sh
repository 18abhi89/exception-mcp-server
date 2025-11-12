#!/bin/bash
# Complete verification script - run this on your local machine

echo "════════════════════════════════════════════════════════════════════════"
echo "COMPLETE SOLUTION VERIFICATION"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "This script will:"
echo "  1. Clear old ChromaDB data"
echo "  2. Reload with fixed code"
echo "  3. Run comprehensive tests"
echo "  4. Give you clear instructions"
echo ""
read -p "Press Enter to continue..."

echo ""
echo "Step 1: Clearing old ChromaDB data..."
echo "────────────────────────────────────────────────────────────────────────"
rm -rf chromadb_data/
echo "✓ Cleared chromadb_data/"

echo ""
echo "Step 2: Reloading database with fixed code..."
echo "────────────────────────────────────────────────────────────────────────"
python clear_and_reload_db.py
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Database reload failed!"
    echo "  Check error messages above."
    exit 1
fi

echo ""
echo "Step 3: Running comprehensive tests..."
echo "────────────────────────────────────────────────────────────────────────"
python test_complete_solution.py
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠ Some tests failed, but key fixes may still work."
    echo "  Check test output above."
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✓ VERIFICATION COMPLETE"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Run: streamlit run streamlit_app.py"
echo "  2. Go to 'Analyze Exception' tab"
echo "  3. Verify dropdown shows ALL 10 exceptions"
echo "  4. Select any exception and click 'Analyze with Historical Data'"
echo "  5. Should see similar cases with confidence scores"
echo ""
echo "Expected results:"
echo "  ✓ Dropdown shows 10 exceptions (not 7)"
echo "  ✓ High Retry Exceptions tab filters correctly"
echo "  ✓ Historical Database tab shows 36 records"
echo "  ✓ Similarity search finds matching cases"
echo ""
echo "If you see any issues, check SOLUTION_SUMMARY.md for details."
echo ""
