#!/usr/bin/env python3
"""
RealSense Camera Script
This script provides RealSense camera functionality for the Docker container.
"""

import sys
import time
import traceback

try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    print("Warning: pyrealsense2 not available")


def check_realsense_devices():
    """Check for available RealSense devices"""
    if not REALSENSE_AVAILABLE:
        print("❌ pyrealsense2 not available")
        return False
    
    try:
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("❌ No RealSense devices found")
            return False
        
        print(f"✅ Found {len(devices)} RealSense device(s):")
        for i, device in enumerate(devices):
            name = device.get_info(rs.camera_info.name)
            serial = device.get_info(rs.camera_info.serial_number)
            firmware = device.get_info(rs.camera_info.firmware_version)
            print(f"  Device {i+1}: {name} (S/N: {serial}, FW: {firmware})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking RealSense devices: {e}")
        return False


def test_realsense_stream():
    """Test RealSense camera stream"""
    if not REALSENSE_AVAILABLE:
        print("❌ Cannot test stream - pyrealsense2 not available")
        return False
    
    try:
        # Configure streams
        pipeline = rs.pipeline()
        config = rs.config()
        
        # Enable depth and color streams
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        
        print("🔄 Starting RealSense pipeline...")
        profile = pipeline.start(config)
        
        print("✅ RealSense pipeline started successfully")
        print("📊 Stream info:")
        
        # Get stream profiles
        depth_profile = profile.get_stream(rs.stream.depth)
        color_profile = profile.get_stream(rs.stream.color)
        
        depth_info = (f"{depth_profile.width()}x{depth_profile.height()} "
                     f"@ {depth_profile.fps()}fps")
        color_info = (f"{color_profile.width()}x{color_profile.height()} "
                     f"@ {color_profile.fps()}fps")
        print(f"  Depth: {depth_info}")
        print(f"  Color: {color_info}")
        
        # Get a few frames to test
        print("📸 Testing frame capture...")
        for i in range(5):
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            
            if depth_frame and color_frame:
                depth_size = f"{depth_frame.get_width()}x{depth_frame.get_height()}"
                color_size = f"{color_frame.get_width()}x{color_frame.get_height()}"
                print(f"  Frame {i+1}: Depth={depth_size}, Color={color_size}")
            else:
                print(f"  Frame {i+1}: Missing frames")
            
            time.sleep(0.5)
        
        pipeline.stop()
        print("✅ RealSense stream test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing RealSense stream: {e}")
        traceback.print_exc()
        return False


def main():
    """Main function for RealSense camera operations"""
    print("🔍 RealSense Camera Test")
    print("=" * 40)
    
    # Check if RealSense is available
    if not REALSENSE_AVAILABLE:
        print("❌ RealSense SDK not available")
        print("   Make sure pyrealsense2 is installed")
        return False
    
    print("✅ RealSense SDK available")
    
    # Check for devices
    if not check_realsense_devices():
        return False
    
    # Test stream
    if not test_realsense_stream():
        return False
    
    print("🎉 All RealSense tests passed!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 