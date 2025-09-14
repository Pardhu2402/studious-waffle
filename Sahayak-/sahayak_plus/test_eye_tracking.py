#!/usr/bin/env python3
"""
Test script to verify eye tracking dependencies
"""

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing eye tracking dependencies...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import mediapipe as mp
        print("✅ MediaPipe imported successfully")
    except ImportError as e:
        print(f"❌ MediaPipe import failed: {e}")
        return False
    
    try:
        import pyautogui
        print("✅ PyAutoGUI imported successfully")
    except ImportError as e:
        print(f"❌ PyAutoGUI import failed: {e}")
        return False
    
    try:
        import websockets
        print("✅ WebSockets imported successfully")
    except ImportError as e:
        print(f"❌ WebSockets import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera availability"""
    print("\nTesting camera access...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ Camera is working and can capture frames")
                print(f"   Frame shape: {frame.shape}")
            else:
                print("❌ Camera opened but cannot capture frames")
                return False
            cap.release()
        else:
            print("❌ Cannot open camera")
            return False
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False
    
    return True

def test_mediapipe():
    """Test MediaPipe face mesh initialization"""
    print("\nTesting MediaPipe Face Mesh...")
    
    try:
        import mediapipe as mp
        
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        print("✅ MediaPipe Face Mesh initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ MediaPipe Face Mesh test failed: {e}")
        return False

if __name__ == "__main__":
    print("Eye Tracking Dependencies Test")
    print("=" * 40)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test camera
        camera_ok = test_camera()
        
        # Test MediaPipe
        mediapipe_ok = test_mediapipe()
        
        print("\n" + "=" * 40)
        if imports_ok and camera_ok and mediapipe_ok:
            print("🎉 All tests passed! Eye tracking system is ready to use.")
            print("\nNext steps:")
            print("1. Start your Sahayak application: python3 app.py")
            print("2. Open the web interface")
            print("3. Press Ctrl+Alt+E to open eye tracking controls")
            print("4. Click 'Connect' to start the eye tracking server")
        else:
            print("❌ Some tests failed. Please check the issues above.")
            print("\nTo install missing dependencies:")
            print("pip3 install -r eye_tracking_requirements.txt")
    else:
        print("\n❌ Import tests failed. Please install dependencies:")
        print("pip3 install -r eye_tracking_requirements.txt")
