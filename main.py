import cv2
import mediapipe as mp
import subprocess
import pyautogui
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "hand_landmarker.task"


# ============================================================
# MediaPipe setup
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

detector = vision.HandLandmarker.create_from_options(options)


# ============================================================
# Camera
# ============================================================

cap = cv2.VideoCapture(0)


# ============================================================
# Gesture variables
# ============================================================

start_x = None

SWIPE_DISTANCE = 0.088
PINCH_DISTANCE = 0.05
SMOOTHING = 0.25

prev_mouse_x = None
prev_mouse_y = None
pinch_active = False


# ============================================================
# Apps
# ============================================================

apps = [
    "Chrome",
    "VS Code",
    "Spotify",
    "File Explorer"
]

selected = 0


# ============================================================
# App commands
# ============================================================

app_commands = {

    "Chrome":
        ["cmd", "/c", "start", "chrome"],

    "VS Code":
        ["code"],

    "Spotify":
        ["cmd", "/c", "start", "spotify:"],

    "File Explorer":
        ["explorer"]
}


# ============================================================
# Function: Launch app
# ============================================================

def launch_app(app_name):

    try:

        subprocess.Popen(
            app_commands[app_name]
        )

        print(f"Launching {app_name}")

    except Exception as e:

        print(f"Could not launch {app_name}")
        print(e)


# ============================================================
# Main loop
# ============================================================

while cap.isOpened():

    success, frame = cap.read()

    if not success:
        break


    # Mirror camera
    frame = cv2.flip(frame, 1)


    # ========================================================
    # Convert BGR → RGB
    # ========================================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )


    # ========================================================
    # Detect hand
    # ========================================================

    result = detector.detect(mp_image)


    gesture_text = "Show your hand"


    # ========================================================
    # Hand detected
    # ========================================================

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]
                    # ====================================================
            # Index finger controls mouse cursor
            # ====================================================

        # ====================================================
# Smooth mouse cursor
# ====================================================

        index_finger = hand[8]

        screen_width, screen_height = pyautogui.size()

        target_x = int(index_finger.x * screen_width)
        target_y = int(index_finger.y * screen_height)


        if prev_mouse_x is None:

            prev_mouse_x = target_x
            prev_mouse_y = target_y


        mouse_x = int(
            prev_mouse_x
            + (target_x - prev_mouse_x) * SMOOTHING
        )

        mouse_y = int(
            prev_mouse_y
            + (target_y - prev_mouse_y) * SMOOTHING
        )


        pyautogui.moveTo(
            mouse_x,
            mouse_y
        )


        prev_mouse_x = mouse_x
        prev_mouse_y = mouse_y

        # ====================================================
        # Pinch detection
        # ====================================================

        thumb = hand[4]
        index = hand[8]

        distance = (
            (thumb.x - index.x) ** 2 +
            (thumb.y - index.y) ** 2
        ) ** 0.5


        # ====================================================
        # PINCH
        # ====================================================

        if distance < PINCH_DISTANCE:

            gesture_text = "PINCH - OPEN"

            cv2.putText(
                frame,
                "PINCH",
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                3
            )


            # Launch only once per pinch
            if not pinch_active:

                app_name = apps[selected]

                launch_app(app_name)

                pinch_active = True


        else:

            pinch_active = False


        # ====================================================
        # Wrist X position
        # ====================================================

        current_x = hand[0].x


        if start_x is None:

            start_x = current_x


        movement = current_x - start_x


        # ====================================================
        # SWIPE RIGHT
        # ====================================================

        if movement > SWIPE_DISTANCE:

            selected += 1

            if selected >= len(apps):

                selected = 0


            start_x = current_x

            gesture_text = "SWIPE RIGHT"


        # ====================================================
        # SWIPE LEFT
        # ====================================================

        elif movement < -SWIPE_DISTANCE:

            selected -= 1

            if selected < 0:

                selected = len(apps) - 1


            start_x = current_x

            gesture_text = "SWIPE LEFT"


        # ====================================================
        # Draw hand landmarks
        # ====================================================

        h, w, _ = frame.shape

        for landmark in hand:

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                5,
                (0, 255, 0),
                -1
            )


    else:

        start_x = None
        pinch_active = False


    # =========================================================
    # UI HEADER
    # =========================================================

    cv2.rectangle(
        frame,
        (0, 0),
        (frame.shape[1], 130),
        (30, 30, 30),
        -1
    )


    cv2.putText(
        frame,
        "AI HAND CONTROLLER",
        (40, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 255, 255),
        3
    )

 
    cv2.putText(
        frame,
        "Swipe LEFT / RIGHT     |     PINCH to OPEN",
        (40, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (200, 200, 200),
        2
    )


    # =========================================================
    # APP CARDS
    # =========================================================

    h, w, _ = frame.shape

    card_width = 190
    card_height = 130

    gap = 25

    total_width = (
        len(apps) * card_width
        + (len(apps) - 1) * gap
    )

    start_card_x = (
        w - total_width
    ) // 2

    card_y = h - 190


    for i, app in enumerate(apps):

        x1 = (
            start_card_x
            + i * (card_width + gap)
        )

        y1 = card_y

        x2 = x1 + card_width
        y2 = y1 + card_height


        # -----------------------------------------------------
        # Selected card
        # -----------------------------------------------------

        if i == selected:

            cv2.rectangle(
                frame,
                (x1 - 5, y1 - 5),
                (x2 + 5, y2 + 5),
                (0, 255, 0),
                4
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (50, 70, 50),
                -1
            )

        else:

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (45, 45, 45),
                -1
            )


        # -----------------------------------------------------
        # App number
        # -----------------------------------------------------

        cv2.putText(
            frame,
            str(i + 1),
            (x1 + 15, y1 + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (180, 180, 180),
            2
        )


        # -----------------------------------------------------
        # App name
        # -----------------------------------------------------

        text_size = cv2.getTextSize(
            app,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            2
        )[0]

        text_x = (
            x1
            + (card_width - text_size[0]) // 2
        )

        text_y = y1 + 80


        cv2.putText(
            frame,
            app,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


    # =========================================================
    # SELECTED APP
    # =========================================================

    selected_text = f"Selected: {apps[selected]}"

    cv2.putText(
        frame,
        selected_text,
        (50, h - 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 0),
        2
    )


    # =========================================================
    # GESTURE STATUS
    # =========================================================

    cv2.putText(
        frame,
        gesture_text,
        (50, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )


    # =========================================================
    # Camera window
    # =========================================================

    cv2.imshow(
        "AI Hand Controller",
        frame
    )


    # =========================================================
    # Keyboard controls
    # =========================================================

    key = cv2.waitKey(1) & 0xFF


    if key == ord("q") or key == 27:

        break


    if cv2.getWindowProperty(
        "AI Hand Controller",
        cv2.WND_PROP_VISIBLE
    ) < 1:

        break


# ============================================================
# Cleanup
# ============================================================

cap.release()

detector.close()

cv2.destroyAllWindows()