#!/usr/bin/env python3
"""
Local test script for the camera hello world functionality
This can be run without Docker to verify the code works.
"""

import sys
import os

# Add the camera directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'camera'))


def test_hello_world():
    """Test the hello world script locally"""
    print("Testing camera hello world script locally...")
    
    try:
        from camera.hello_world import main
        print("✓ Successfully imported hello_world module")
        
        # Run the main function
        main()
        print("✓ Hello world script executed successfully")
        
    except ImportError as e:
        print(f"✗ Failed to import hello_world module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error running hello_world script: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_hello_world()
    if success:
        print("\n🎉 All tests passed! The camera container is ready to build.")
    else:
        print("\n❌ Tests failed. Please check the code.")
        sys.exit(1) 