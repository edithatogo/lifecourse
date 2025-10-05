import unittest
import sys
import os

# Add the 'src' directory to the Python path to resolve import errors
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

print("--- sys.path ---")
for p in sys.path:
    print(p)
print("----------------")

print("\n--- Attempting direct imports ---")
try:
    print("Successfully imported advanced_analysis")
    print("Successfully imported cohort")
    print("Successfully imported data_loader")
except Exception as e:
    print(f"Direct import failed: {e}")
print("---------------------------------")


if __name__ == "__main__":
    # Discover and run all tests in the 'tests' directory
    loader = unittest.TestLoader()
    suite = loader.discover("tests")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with a non-zero status code if any tests failed
    if not result.wasSuccessful():
        sys.exit(1)
