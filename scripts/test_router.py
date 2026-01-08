#!/usr/bin/env python3
"""
Antigravity Router Test CLI
===========================
System: Engram Context Ecology Platform

Test the routing logic and optionally process files.

Usage:
    # Test classification only (no processing)
    python scripts/test_router.py --file safety_manual.pdf --dry-run
    
    # Full processing with output
    python scripts/test_router.py --file meeting_notes.docx
    
    # Test mode with generated dummy files
    python scripts/test_router.py --test-mode
"""

import argparse
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def print_classification(filename: str, data_class, reason: str):
    """Pretty print classification result."""
    class_emoji = {
        "CLASS_A_TRUTH": "📚",
        "CLASS_B_CHATTER": "💬", 
        "CLASS_C_OPS": "📊",
    }
    emoji = class_emoji.get(data_class.name, "❓")
    
    print(f"\n{emoji} Classification: {filename}")
    print(f"   Data Class: {data_class.name}")
    print(f"   Reason: {reason}")
    print(f"   Value: {data_class.value}")


def test_classification_only(file_path: str):
    """Test classification without processing."""
    from backend.etl.antigravity_router import antigravity_router
    
    data_class, reason = antigravity_router.classify(file_path)
    print_classification(Path(file_path).name, data_class, reason)
    return data_class


def test_full_processing(file_path: str):
    """Test full ingestion pipeline."""
    from backend.etl.antigravity_router import antigravity_router
    
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    data_class, reason = antigravity_router.classify(file_path)
    print_classification(path.name, data_class, reason)
    
    print("\n📥 Processing...")
    try:
        chunks = antigravity_router.ingest(file_path)
        
        print(f"✅ Ingestion Complete")
        print(f"   Chunks generated: {len(chunks)}")
        
        if chunks:
            first = chunks[0]
            print(f"\n   Sample chunk:")
            print(f"   - Text (first 100 chars): {first['text'][:100]}...")
            print(f"   - Data Class: {first['metadata'].get('data_class', 'unknown')}")
            print(f"   - Decay Rate: {first['metadata'].get('decay_rate', 'unknown')}")
            print(f"   - Provenance ID: {first['metadata'].get('provenance_id', 'unknown')}")
        
        return chunks
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_test_mode():
    """Run tests with generated dummy files."""
    import tempfile
    
    print("🧪 Antigravity Router Test Mode\n")
    print("=" * 50)
    
    from backend.etl.antigravity_router import antigravity_router, DataClass
    
    # Test cases: (filename, expected_class)
    test_cases = [
        ("safety_manual.pdf", DataClass.CLASS_A_TRUTH),
        ("iso_9001_standard.pdf", DataClass.CLASS_A_TRUTH),
        ("random_document.pdf", DataClass.CLASS_A_TRUTH),  # Default for PDF
        ("meeting_notes.docx", DataClass.CLASS_B_CHATTER),
        ("presentation.pptx", DataClass.CLASS_B_CHATTER),
        ("email_thread.eml", DataClass.CLASS_B_CHATTER),
        ("webpage.html", DataClass.CLASS_B_CHATTER),
        ("sensor_data.csv", DataClass.CLASS_C_OPS),
        ("api_response.json", DataClass.CLASS_C_OPS),
        ("analytics.parquet", DataClass.CLASS_C_OPS),
        ("unknown.xyz", DataClass.CLASS_B_CHATTER),  # Fallback
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected in test_cases:
        data_class, reason = antigravity_router.classify(filename)
        
        if data_class == expected:
            print(f"✅ {filename:30} -> {data_class.name}")
            passed += 1
        else:
            print(f"❌ {filename:30} -> {data_class.name} (expected {expected.name})")
            failed += 1
    
    print("=" * 50)
    print(f"\n📊 Results: {passed}/{len(test_cases)} passed")
    
    # Test actual processing with a dummy text file
    print("\n" + "=" * 50)
    print("📥 Testing actual processing with dummy file...\n")
    
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', delete=False
    ) as tmp:
        tmp.write("Meeting notes: The H-Class turbine showed vibration anomalies during Phase 2 startup.")
        tmp_path = tmp.name
    
    try:
        chunks = antigravity_router.ingest(tmp_path, filename="meeting_notes.txt")
        print(f"✅ Processed {tmp_path}")
        print(f"   Chunks: {len(chunks)}")
        if chunks:
            meta = chunks[0]["metadata"]
            print(f"   Data Class: {meta.get('data_class')}")
            print(f"   Has Provenance: {'provenance_id' in meta}")
    except Exception as e:
        print(f"⚠️ Processing test skipped (dependencies may be missing): {e}")
    finally:
        os.unlink(tmp_path)
    
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Test Antigravity Ingestion Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify a file (no processing)
  python scripts/test_router.py --file manual.pdf --dry-run
  
  # Process a file
  python scripts/test_router.py --file notes.docx
  
  # Run all tests
  python scripts/test_router.py --test-mode
"""
    )
    
    parser.add_argument("-f", "--file", help="File to classify/process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only classify, don't process")
    parser.add_argument("--test-mode", action="store_true",
                        help="Run automated tests")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    
    args = parser.parse_args()
    
    if args.test_mode:
        success = run_test_mode()
        sys.exit(0 if success else 1)
    
    if not args.file:
        parser.print_help()
        sys.exit(1)
    
    if args.dry_run:
        test_classification_only(args.file)
    else:
        chunks = test_full_processing(args.file)
        if args.json and chunks:
            print("\n📋 JSON Output:")
            print(json.dumps(chunks[:3], indent=2, default=str))


if __name__ == "__main__":
    main()
