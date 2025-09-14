import asyncio
import websockets
import json
import cv2
import mediapipe as mp
import pyautogui
import logging
import signal
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
cam = None
face_mesh = None
blink_sensitivity = 0.004
move_sensitivity = 1.0

def initialize_tracking():
    """Initialize camera and MediaPipe"""
    global cam, face_mesh
    
    try:
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            logger.error("Cannot open camera")
            return False
        
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        logger.info("MediaPipe Face Mesh initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize camera or MediaPipe: {e}")
        return False

def cleanup():
    """Clean up resources"""
    global cam
    if cam and cam.isOpened():
        cam.release()
    cv2.destroyAllWindows()
    logger.info("Resources cleaned up")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Shutting down...")
    cleanup()
    sys.exit(0)

async def eye_tracking_handler(websocket):
    """Handle eye tracking for a single client"""
    global blink_sensitivity, move_sensitivity, cam, face_mesh
    
    logger.info(f"Client connected: {websocket.remote_address}")
    
    try:
        while True:
            # Check for incoming messages (settings updates)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.001)
                msg = json.loads(message)
                if 'settings' in msg:
                    blink_sensitivity = float(msg['settings'].get('blink', blink_sensitivity))
                    move_sensitivity = float(msg['settings'].get('move', move_sensitivity))
                    logger.info(f"Updated settings: blink={blink_sensitivity}, move={move_sensitivity}")
            except asyncio.TimeoutError:
                pass  # No message received, continue with tracking
            except websockets.exceptions.ConnectionClosed:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
            # Capture and process frame
            ret, frame = cam.read()
            if not ret:
                logger.error("Failed to capture frame")
                continue
                
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            try:
                output = face_mesh.process(rgb_frame)
                landmark_points = output.multi_face_landmarks
                
                data = {}
                if landmark_points:
                    landmarks = landmark_points[0].landmark
                    
                    # Use nose tip for more stable gaze tracking
                    gaze_x = landmarks[9].x
                    gaze_y = landmarks[9].y
                    
                    # Apply movement sensitivity
                    gaze_x = (gaze_x - 0.5) * move_sensitivity + 0.5
                    gaze_y = (gaze_y - 0.5) * move_sensitivity + 0.5
                    gaze_x = min(max(gaze_x, 0), 1)
                    gaze_y = min(max(gaze_y, 0), 1)
                    
                    data['gaze'] = {
                        'x': gaze_x,
                        'y': gaze_y
                    }
                    
                    # Blink detection using left eye landmarks
                    left_eye_top = landmarks[159]
                    left_eye_bottom = landmarks[145]
                    eye_height = abs(left_eye_top.y - left_eye_bottom.y)
                    
                    data['wink'] = eye_height < blink_sensitivity
                    data['face_detected'] = True
                else:
                    data['face_detected'] = False
                    data['wink'] = False
                    
                # Send data to client
                await websocket.send(json.dumps(data))
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                data = {'face_detected': False, 'wink': False}
                await websocket.send(json.dumps(data))
                
            # Control frame rate (~30 FPS)
            await asyncio.sleep(0.033)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error in eye_tracking: {e}")

async def main():
    """Main function to start the WebSocket server"""
    if not initialize_tracking():
        logger.error("Failed to initialize tracking, exiting...")
        return
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Get screen dimensions
        screen_w, screen_h = pyautogui.size()
        logger.info(f"Screen size: {screen_w}x{screen_h}")
        
        # Start WebSocket server
        async with websockets.serve(eye_tracking_handler, 'localhost', 8765):
            logger.info("WebSocket eye tracking server started on ws://localhost:8765")
            logger.info("Press Ctrl+C to stop the server")
            
            # Run forever
            await asyncio.Future()
            
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        cleanup()
