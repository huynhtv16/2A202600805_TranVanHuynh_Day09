#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script for RAG Chatbot.

Usage:
    python test_chatbot.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

load_dotenv()

# ===========================================================================
# TEST 1: Check imports
# ===========================================================================

print("=" * 70)
print("TEST 1: Checking imports...")
print("=" * 70)

try:
    import streamlit
    print("✅ streamlit OK")
except ImportError as e:
    print(f"❌ streamlit: {e}")

try:
    import google.generativeai
    print("✅ google-generativeai OK")
except ImportError as e:
    print(f"❌ google-generativeai: {e}")

try:
    from src.task9_retrieval_pipeline import retrieve
    print("✅ retrieval pipeline OK")
except ImportError as e:
    print(f"❌ retrieval pipeline: {e}")

try:
    from src.task10_generation import generate_with_citation, format_context
    print("✅ generation module OK")
except ImportError as e:
    print(f"❌ generation module: {e}")

# ===========================================================================
# TEST 2: Check API key
# ===========================================================================

print("\n" + "=" * 70)
print("TEST 2: Checking API key...")
print("=" * 70)

api_key = os.getenv("GEMINI_API_KEY", "")
if api_key:
    masked = api_key[:10] + "..." + api_key[-5:]
    print(f"✅ GEMINI_API_KEY found: {masked}")
else:
    print("❌ GEMINI_API_KEY not found in .env")

# ===========================================================================
# TEST 3: Test Gemini API
# ===========================================================================

print("\n" + "=" * 70)
print("TEST 3: Testing Gemini API...")
print("=" * 70)

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    # Try different model names
    models_to_try = ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
    model = None
    working_model = None
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Xin chào! Bạn tên gì?")
            working_model = model_name
            print(f"✅ Gemini API works with model: {working_model}")
            print(f"Response sample: {response.text[:100]}...")
            break
        except Exception:
            continue
    
    if not working_model:
        print("❌ No Gemini models available")
except Exception as e:
    print(f"❌ Gemini API error: {e}")

# ===========================================================================
# TEST 4: Test Retrieval
# ===========================================================================

print("\n" + "=" * 70)
print("TEST 4: Testing Retrieval Pipeline...")
print("=" * 70)

try:
    from src.task9_retrieval_pipeline import retrieve
    
    results = retrieve("luật phòng chống ma tuý", top_k=3)
    
    if results:
        print(f"✅ Retrieved {len(results)} documents")
        for i, doc in enumerate(results, 1):
            print(f"\n  [{i}] {doc.get('metadata', {}).get('source', 'Unknown')}")
            print(f"      Score: {doc.get('score', 0):.3f}")
            print(f"      Content: {doc.get('content', '')[:80]}...")
    else:
        print("❌ No results from retrieval")
except Exception as e:
    print(f"❌ Retrieval error: {e}")

# ===========================================================================
# TEST 5: Test Generation
# ===========================================================================

print("\n" + "=" * 70)
print("TEST 5: Testing Generation...")
print("=" * 70)

try:
    from src.task10_generation import generate_with_citation
    
    result = generate_with_citation("Luật phòng chống ma tuý bao gồm những gì?", top_k=3)
    
    if result:
        print("✅ Generation works!")
        print(f"Answer: {result.get('answer', '')[:200]}...")
        print(f"Sources: {len(result.get('sources', []))} documents")
    else:
        print("❌ Generation returned None")
except Exception as e:
    print(f"❌ Generation error: {e}")

# ===========================================================================
# TEST 6: Streamlit Check
# ===========================================================================

print("\n" + "=" * 70)
print("TEST 6: Streamlit App File...")
print("=" * 70)

app_file = ROOT_DIR / "streamlit_app.py"
if app_file.exists():
    print(f"✅ {app_file} exists")
    print("\nTo run the chatbot, use:")
    print("  streamlit run streamlit_app.py")
else:
    print(f"❌ {app_file} not found")

# ===========================================================================
# SUMMARY
# ===========================================================================

print("\n" + "=" * 70)
print("✅ All tests passed! You can now run:")
print("   streamlit run streamlit_app.py")
print("=" * 70)
