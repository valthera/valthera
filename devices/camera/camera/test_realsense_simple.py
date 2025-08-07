#!/usr/bin/env python3
"""
Simple RealSense Test Script
This script tests RealSense functionality and will work on both Mac
(container) and Jetson Nano.
"""

import sys


def test_realsense_import():
    """Test if pyrealsense2 can be imported"""
    try:
        import pyrealsense2 as rs  # noqa: F401
        print("✅ pyrealsense2 imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import pyrealsense2: {e}")
        return False


def test_realsense_context():
    """Test RealSense context creation"""
    try:
        import pyrealsense2 as rs
        ctx = rs.context()  # noqa: F841
        print("✅ RealSense context created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create RealSense context: {e}")
        return False


def test_realsense_devices():
    """Test RealSense device detection"""
    try:
        import pyrealsense2 as rs
        ctx = rs.context()
        devices = ctx.query_devices()
        
        print(f"📊 Found {len(devices)} RealSense device(s)")
        
        if len(devices) == 0:
            print("⚠️  No RealSense devices found")
            print("   This is expected on Mac (Docker limitations)")
            print("   Will work on Jetson Nano with connected camera")
            return False
        
        for i, device in enumerate(devices):
            try:
                name = device.get_info(rs.camera_info.name)
                serial = device.get_info(rs.camera_info.serial_number)
                firmware = device.get_info(rs.camera_info.firmware_version)
                print(f"  Device {i+1}: {name} (S/N: {serial}, "
                      f"FW: {firmware})")
            except Exception as e:
                print(f"  Device {i+1}: Error getting info: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error detecting RealSense devices: {e}")
        return False


def main():
    """Main test function"""
    print("🔍 Simple RealSense Test")
    print("=" * 30)
    
    # Test 1: Import
    if not test_realsense_import():
        return False
    
    # Test 2: Context
    if not test_realsense_context():
        return False
    
    # Test 3: Devices
    devices_found = test_realsense_devices()
    
    print("\n📋 Summary:")
    print("✅ RealSense SDK is working")
    if devices_found:
        print("✅ RealSense camera detected")
        print("🎉 Ready for RealSense development!")
    else:
        print("⚠️  No RealSense camera detected")
        print("   This is normal on Mac (Docker limitations)")
        print("   Will work on Jetson Nano with camera")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 