"""
Quick test to verify core functionality without API calls
"""
from core import extract_duration_days_full, words_to_number

def test_fallback_extractor():
    """Test the local regex-based extractor"""
    tests = [
        ("7 days", 7),
        ("weekend trip", 2),
        ("a 10-day vacation", 10),
        ("one week", 7),
        ("two weeks", 14),
        ("a week and a half", 11),
        ("10-12 days", 10),
        ("five days", 5),
        ("3 nights", 3),
    ]
    
    print("Testing fallback extractor:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for query, expected in tests:
        result = extract_duration_days_full(query)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] '{query}' -> {result} (expected {expected})")
    
    print("-" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

def test_word_conversion():
    """Test number word conversion"""
    tests = [
        ("one", 1),
        ("five", 5),
        ("ten", 10),
        ("twenty", 20),
        ("seven", 7),
    ]
    
    print("\nTesting word-to-number conversion:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for word, expected in tests:
        result = words_to_number(word)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] '{word}' -> {result} (expected {expected})")
    
    print("-" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    print("=" * 50)
    print("BASIC FUNCTIONALITY TEST")
    print("=" * 50)
    
    test1_ok = test_fallback_extractor()
    test2_ok = test_word_conversion()
    
    print("\n" + "=" * 50)
    if test1_ok and test2_ok:
        print("SUCCESS: ALL TESTS PASSED")
    else:
        print("FAILURE: SOME TESTS FAILED")
    print("=" * 50)
