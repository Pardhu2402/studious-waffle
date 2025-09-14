# Eye Tracking Integration Guide for Sahayak+

## Overview
This guide will help you set up and use the eye tracking accessibility feature in your Sahayak+ application. The eye tracking system provides hands-free navigation and control using eye movements and blinks.

## Features
- **Real-time Eye Cursor**: Visual cursor that follows your eye movements
- **Blink Detection**: Click functionality using blinks
- **Adjustable Settings**: Sensitivity, smoothing, and click threshold controls
- **Floating Overlay**: Works across all pages of your Sahayak application
- **Keyboard Shortcuts**: Quick access controls
- **Status Indicators**: Real-time connection and tracking status

## Installation

### 1. Install Dependencies
First, install the required Python packages:

```bash
# Navigate to your Sahayak directory
cd "/Users/pardhu/vsc/sarathi/sign language/Sahayak-/sahayak_plus"

# Install eye tracking dependencies
pip3 install -r eye_tracking_requirements.txt
```

### 2. Verify Installation
Test that all dependencies are installed correctly:

```bash
python3 -c "import cv2, mediapipe, pyautogui, websockets; print('All dependencies installed successfully!')"
```

### 3. Camera Permissions
Make sure your system has camera permissions enabled for Python/Terminal applications.

**On macOS:**
- Go to System Preferences → Security & Privacy → Privacy → Camera
- Add Terminal or your Python interpreter to allowed applications

## Usage

### Starting the System

1. **Start your Sahayak application:**
   ```bash
   python3 app.py
   ```

2. **Access the Eye Tracking Overlay:**
   - The overlay will automatically appear when you load any Sahayak page
   - Use keyboard shortcut `Ctrl+Alt+E` to toggle the control panel
   - Use keyboard shortcut `Ctrl+Alt+M` to start/stop tracking

### Using the Control Panel

The floating control panel appears in the top-right corner and includes:

- **Connect Button**: Connects to the eye tracking server
- **Start/Stop Tracking**: Begins or ends eye cursor tracking
- **Sensitivity Slider**: Adjusts cursor movement sensitivity (0.5-2.0)
- **Blink Sensitivity**: Controls blink detection threshold (0.002-0.008)
- **Smoothing**: Reduces cursor jitter (0.1-0.9)
- **Auto-click Toggle**: Enable/disable clicking on blink

### Step-by-Step Usage

1. **Connect to Server:**
   - Click the "Connect" button in the control panel
   - The system will automatically start the WebSocket server
   - Wait for the "Connected" status message

2. **Start Eye Tracking:**
   - Click "Start Tracking" button
   - Grant camera permission when prompted
   - The blue eye cursor will appear and follow your eye movements

3. **Adjust Settings:**
   - Use the sliders to fine-tune sensitivity and smoothing
   - Enable "Auto-click on blink" for hands-free clicking
   - Adjust blink sensitivity if clicks are too sensitive or not responsive enough

4. **Navigate:**
   - Look at different parts of the screen to move the cursor
   - Blink to click on buttons, links, and other elements
   - Use the large scroll buttons on the right side for page navigation

### Keyboard Shortcuts

- `Ctrl+Alt+E`: Toggle control panel visibility
- `Ctrl+Alt+M`: Start/stop eye tracking (connects automatically if needed)

## Troubleshooting

### Common Issues

**"Failed to connect" error:**
- Make sure no other application is using the camera
- Check that all dependencies are installed correctly
- Restart the Sahayak application

**Eye cursor not appearing:**
- Ensure you clicked "Start Tracking" after connecting
- Check camera permissions in system settings
- Try adjusting the sensitivity settings

**Cursor movement is jittery:**
- Increase the "Smoothing" value (try 0.7-0.8)
- Ensure good lighting conditions
- Sit at a consistent distance from the camera

**Clicks not working:**
- Adjust the "Blink Sensitivity" slider
- Make sure "Auto-click on blink" is enabled
- Try deliberate, slow blinks rather than natural blinking

**Poor tracking accuracy:**
- Ensure good lighting (avoid backlighting)
- Position yourself 18-24 inches from the camera
- Keep your head relatively stable
- Clean your camera lens

### Performance Tips

1. **Optimal Setup:**
   - Good, even lighting on your face
   - Camera at eye level
   - Minimal background movement
   - Stable seating position

2. **Settings Recommendations:**
   - **Sensitivity**: Start with 1.0, adjust based on screen size
   - **Blink Sensitivity**: 0.004 works for most users
   - **Smoothing**: 0.7 provides good balance of responsiveness and stability

3. **System Requirements:**
   - Built-in or external webcam
   - Python 3.8 or newer
   - Sufficient lighting conditions

## Technical Details

### Architecture
- **WebSocket Server**: Runs on `ws://localhost:8765`
- **Computer Vision**: Uses MediaPipe for facial landmark detection
- **Frontend**: JavaScript overlay with real-time cursor updates
- **Integration**: Works seamlessly with existing Sahayak Flask routes

### Security & Privacy
- All processing happens locally on your machine
- No video data is stored or transmitted over the internet
- Camera access is only used for real-time eye tracking
- WebSocket server only accepts local connections

## Advanced Configuration

### Customizing Settings
You can modify default settings in the JavaScript file:
```javascript
// In static/js/eye_control.js
this.settings = {
    sensitivity: 1.0,        // Cursor movement sensitivity
    blink_threshold: 0.004,  // Blink detection sensitivity
    smoothing: 0.7,          // Movement smoothing factor
    auto_click: true         // Enable blink clicking
};
```

### Server Configuration
The WebSocket server runs on port 8765 by default. To change this, modify:
```python
# In eye_tracking_server.py
websockets.serve(eye_server.handle_client, "localhost", 8765)
```

## Support

If you encounter issues:

1. Check the browser console for JavaScript errors
2. Verify all Python dependencies are installed
3. Ensure camera permissions are granted
4. Try restarting both the Sahayak app and your browser
5. Test with different lighting conditions

## Accessibility Benefits

This eye tracking system provides:
- **Motor Accessibility**: Hands-free navigation for users with limited mobility
- **Alternative Input Method**: Backup navigation when traditional input is difficult
- **Enhanced User Experience**: Innovative interaction method for all users
- **Educational Access**: Better access to Sahayak's learning content

---

The eye tracking system is now fully integrated into your Sahayak+ application and ready to use!
