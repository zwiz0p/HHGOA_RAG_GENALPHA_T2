import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pipeline import orchestrator


def test_dual_mode_qa():
    print("\n--- 1. Testing Grounded In-Domain Query (Knowledge Base) ---")
    res_kb = orchestrator.run(query_text="Who directed the Los Alamos Laboratory during the Manhattan Project?")
    print(f"Answer     : {res_kb.answer}")
    print(f"Source Type: {res_kb.source_type}")
    print(f"Grounded   : {res_kb.grounded}")
    print(f"Confidence : {res_kb.confidence}")
    print(f"Sources    : {len(res_kb.sources)} chunks")
    assert res_kb.source_type == "knowledge_base"
    assert res_kb.grounded is True
    assert res_kb.blocked is False
    assert len(res_kb.sources) > 0

    print("\n--- 2. Testing Out-of-Domain General Knowledge Query (Hindi Fallback) ---")
    res_gen = orchestrator.run(query_text="भारत की राजधानी क्या है?")
    print(f"Answer     : {res_gen.answer}")
    print(f"Source Type: {res_gen.source_type}")
    print(f"Grounded   : {res_gen.grounded}")
    print(f"Confidence : {res_gen.confidence}")
    assert res_gen.source_type == "general_knowledge"
    assert res_gen.grounded is False
    assert res_gen.blocked is False
    assert "General World Knowledge" in res_gen.answer or "Not found in indexed" in res_gen.answer

    print("\n--- 3. Testing Recipe General Knowledge Query (English Fallback) ---")
    res_recipe = orchestrator.run(query_text="How to make a masala omelette step by step?")
    print(f"Answer     : {res_recipe.answer}")
    print(f"Source Type: {res_recipe.source_type}")
    print(f"Grounded   : {res_recipe.grounded}")
    assert res_recipe.source_type == "general_knowledge"
    assert res_recipe.grounded is False
    assert res_recipe.blocked is False

    print("\n--- 4. Testing Fast-Path Intent Router ---")
    res_fp = orchestrator.run(query_text="Namaste")
    print(f"Answer     : {res_fp.answer}")
    print(f"Source Type: {res_fp.source_type}")
    print(f"Confidence : {res_fp.confidence}")
    assert res_fp.source_type == "fast_path"
    assert res_fp.confidence == 1.0

    print("\n[OK] All Dual-Mode Tests Passed Successfully!")


if __name__ == "__main__":
    test_dual_mode_qa()
