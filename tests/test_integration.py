import os
import sys
import logging

# Add project root and backend to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_path = os.path.join(root_path, "src", "backend")
sys.path.insert(0, root_path)
sys.path.insert(0, backend_path)

from src.backend.main import main

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

if __name__ == "__main__":
    print("!!! STARTING FULL E2E INTEGRATION TEST !!!")
    try:
        main()
        print("\n!!! INTEGRATION TEST COMPLETED SUCCESSFULLY !!!")
    except Exception as e:
        print(f"\n!!! INTEGRATION TEST FAILED: {e} !!!")
        import traceback
        traceback.print_exc()
