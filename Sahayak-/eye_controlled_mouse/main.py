import cv2
import mediapipe as mp
import pyautogui

cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()

# Button parameters
button_width = 120
button_height = 120
button_alpha = 0.3  # Transparency (0.0 to 1.0)
margin = 40

while True:
    _, frame = cam.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb_frame)
    landmark_points = output.multi_face_landmarks
    frame_h, frame_w, _ = frame.shape

    # Button positions (right side, vertically spaced)
    up_btn_x1 = frame_w - button_width - margin
    up_btn_y1 = int(frame_h * 0.25)
    up_btn_x2 = up_btn_x1 + button_width
    up_btn_y2 = up_btn_y1 + button_height

    down_btn_x1 = frame_w - button_width - margin
    down_btn_y1 = int(frame_h * 0.65)
    down_btn_x2 = down_btn_x1 + button_width
    down_btn_y2 = down_btn_y1 + button_height

    # Draw transparent buttons
    overlay = frame.copy()
    cv2.rectangle(overlay, (up_btn_x1, up_btn_y1), (up_btn_x2, up_btn_y2), (255, 255, 255), -1)
    cv2.rectangle(overlay, (down_btn_x1, down_btn_y1), (down_btn_x2, down_btn_y2), (255, 255, 255), -1)
    frame = cv2.addWeighted(overlay, button_alpha, frame, 1 - button_alpha, 0)

    # Draw arrows
    cv2.putText(frame, '↑', (up_btn_x1 + 35, up_btn_y1 + 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 100, 255), 6)
    cv2.putText(frame, '↓', (down_btn_x1 + 35, down_btn_y1 + 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 100, 255), 6)

    cursor_x, cursor_y = None, None
    if landmark_points:
        landmarks = landmark_points[0].landmark
        for id, landmark in enumerate(landmarks[474:478]):
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (0, 255, 0))
            if id == 1:
                screen_x = screen_w * landmark.x
                screen_y = screen_h * landmark.y
                pyautogui.moveTo(screen_x, screen_y)
                cursor_x, cursor_y = x, y  # Save for blink check

        left = [landmarks[145], landmarks[159]]
        for landmark in left:
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255))

        # Blink detection
        if (left[0].y - left[1].y) < 0.004:
            # Check if gaze/cursor is over scroll up button
            if cursor_x is not None and cursor_y is not None:
                if up_btn_x1 < cursor_x < up_btn_x2 and up_btn_y1 < cursor_y < up_btn_y2:
                    pyautogui.scroll(300)  # Scroll up
                    pyautogui.sleep(1)
                # Check if gaze/cursor is over scroll down button
                elif down_btn_x1 < cursor_x < down_btn_x2 and down_btn_y1 < cursor_y < down_btn_y2:
                    pyautogui.scroll(-300)  # Scroll down
                    pyautogui.sleep(1)
                else:
                    pyautogui.click()
                    pyautogui.sleep(1)

    cv2.imshow('Eye Controlled Mouse', frame)
    cv2.waitKey(1)