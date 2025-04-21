import cv2
import mediapipe as mp
import numpy as np
import random
import time
import math

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if not ret:
    exit()

frame_h, frame_w = frame.shape[:2]

# Constants for eye landmarks
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Constants for calibration and control
CALIBRATION_FRAMES = 60  
SMOOTHING_FACTOR = 0.4
CLICK_KEY = ord(' ')  
CLICK_COOLDOWN = 0.2

# Eye movement sensitivity
EYE_MOVEMENT_MULTIPLIER = 5.0

# OSU Game parameters
CIRCLE_RADIUS = 50
CIRCLE_LIFETIME = 2.0  # seconds
CIRCLE_APPROACH_TIME = 1.5  # seconds
MAX_CIRCLES = 10

# Scoring parameters
SCORE_PERFECT = 300
SCORE_GREAT = 200
SCORE_OK = 100
SCORE_MEH = 50
SCORE_MISS = -100

# Timing windows
PERFECT_WINDOW = 0.1  # Within 0.1s of ideal time
GREAT_WINDOW = 0.2
OK_WINDOW = 0.3
MEH_WINDOW = 0.4

# Game state variables
game_objects = []  # (x, y, birth_time, hit, hit_quality)
cursor_x, cursor_y = frame_w // 2, frame_h // 2
score = 0
combo = 0
last_spawn_time = 0
spawn_interval = 1.5  # seconds
last_click_time = 0
game_active = False  # Game starts only after calibration
feedback_messages = []  # List of (x, y, message, color, birth_time)

# Variables for tracking
calibration_frames = 0
center_x, center_y = 0, 0
both_eyes_closed_frames = 0

def get_iris_center(landmarks, iris_indices):
    iris_points = []
    for idx in iris_indices:
        point = landmarks[idx]
        iris_points.append([point.x, point.y])
    iris_points = np.array(iris_points)
    center = np.mean(iris_points, axis=0)
    return center

def calculate_eye_aspect_ratio(landmarks, eye_indices):
    points = []
    for index in eye_indices:
        point = landmarks[index]
        points.append([point.x, point.y])
    points = np.array(points)
    vertical_1 = np.linalg.norm(points[1] - points[5])
    vertical_2 = np.linalg.norm(points[2] - points[4])
    horizontal = np.linalg.norm(points[0] - points[3])
    if horizontal == 0:
        return 0
    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return ear

def spawn_game_object():
    margin = CIRCLE_RADIUS * 2
    x = random.randint(margin, frame_w - margin)
    y = random.randint(margin, frame_h - margin)
    birth_time = time.time()
    game_objects.append([x, y, birth_time, False, None])

def add_feedback_message(x, y, message, color):
    """Add a feedback message that will be displayed for a short time"""
    feedback_messages.append([x, y, message, color, time.time()])

def draw_circle_object(frame, obj):
    x, y, birth_time, hit, hit_quality = obj
    current_time = time.time()
    age = current_time - birth_time
    if age > CIRCLE_LIFETIME:
        return False
    if hit:
        hit_progress = min(1.0, (current_time - birth_time) / 0.3)
        radius = int(CIRCLE_RADIUS * (1 + hit_progress))
        alpha = max(0, 1 - hit_progress)
        overlay = frame.copy()
        if hit_quality == "PERFECT":
            color = (0, 255, 255)
        elif hit_quality == "GREAT":
            color = (0, 255, 0)
        elif hit_quality == "OK":
            color = (0, 165, 255)
        elif hit_quality == "MEH":
            color = (0, 0, 255)
        else:
            color = (255, 0, 255)
        cv2.circle(overlay, (x, y), radius, color, 2)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        return hit_progress < 1.0
    else:
        approach_progress = min(1.0, age / CIRCLE_APPROACH_TIME)
        approach_radius = int(CIRCLE_RADIUS * (3 - 2 * approach_progress))
        cv2.circle(frame, (x, y), approach_radius, (255, 255, 255), 2)
        cv2.circle(frame, (x, y), CIRCLE_RADIUS, (255, 0, 255), 2)
        object_index = next((i for i, o in enumerate(game_objects) if o[0] == x and o[1] == y and o[2] == birth_time), -1)
        if object_index != -1:
            cv2.putText(frame, str(object_index + 1), 
                      (x-10, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return True

def draw_feedback_messages(frame):
    """Draw temporary feedback messages"""
    current_time = time.time()
    global feedback_messages
    new_messages = []
    for msg in feedback_messages:
        x, y, text, color, birth_time = msg
        age = current_time - birth_time
        if age <= 1.0:
            alpha = max(0, 1 - age)
            overlay = frame.copy()
            cv2.putText(overlay, text, (x-len(text)*4, y), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
            new_messages.append(msg)
    feedback_messages = new_messages

def check_hit(x, y):
    global score, combo
    current_time = time.time()
    hit_any = False
    hit_quality = None
    hit_index = -1
    for i, obj in enumerate(game_objects):
        obj_x, obj_y, birth_time, hit, _ = obj
        if hit:
            continue
        distance = math.sqrt((x - obj_x)**2 + (y - obj_y)**2)
        if distance <= CIRCLE_RADIUS:
            age = current_time - birth_time
            ideal_hit_time = CIRCLE_APPROACH_TIME
            timing_diff = abs(age - ideal_hit_time)
            points = 0
            if timing_diff <= PERFECT_WINDOW:
                hit_quality = "PERFECT"
                points = SCORE_PERFECT
            elif timing_diff <= GREAT_WINDOW:
                hit_quality = "GREAT"
                points = SCORE_GREAT
            elif timing_diff <= OK_WINDOW:
                hit_quality = "OK"
                points = SCORE_OK 
            elif timing_diff <= MEH_WINDOW:
                hit_quality = "MEH"
                points = SCORE_MEH
            else:
                hit_quality = "MEH"
                points = SCORE_MEH
            game_objects[i][3] = True
            game_objects[i][4] = hit_quality
            add_feedback_message(obj_x, obj_y, hit_quality, get_color_for_hit_quality(hit_quality))
            score += points
            combo += 1
            hit_any = True
            hit_index = i
            break
    return hit_any, hit_quality, hit_index

def get_color_for_hit_quality(hit_quality):
    """Get color for hit quality feedback"""
    if hit_quality == "PERFECT":
        return (0, 255, 255)
    elif hit_quality == "GREAT":
        return (0, 255, 0)
    elif hit_quality == "OK":
        return (0, 165, 255)
    elif hit_quality == "MEH":
        return (0, 0, 255)
    else:
        return (255, 0, 255)

def cleanup_game_objects():
    global combo, score
    current_time = time.time()
    new_objects = []
    for obj in game_objects:
        x, y, birth_time, hit, hit_quality = obj
        age = current_time - birth_time
        if (hit and age <= CIRCLE_LIFETIME + 0.3) or (not hit and age <= CIRCLE_LIFETIME):
            new_objects.append(obj)
        elif not hit and age > CIRCLE_LIFETIME:
            score += SCORE_MISS
            combo = 0
            add_feedback_message(x, y, "MISS", (0, 0, 255))
    return new_objects

def draw_calibration_message(frame, progress):
    overlay = frame.copy()
    box_margin = 20
    box_height = 180
    cv2.rectangle(overlay, 
                 (box_margin, frame_h//2 - box_height//2), 
                 (frame_w - box_margin, frame_h//2 + box_height//2), 
                 (40, 40, 40), -1)
    alpha = 0.7
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.putText(frame, "CALIBRATION IN PROGRESS", 
               (frame_w//2 - 180, frame_h//2 - 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Please keep your head still and look straight ahead", 
               (frame_w//2 - 250, frame_h//2 - 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    bar_width = frame_w - 2 * box_margin - 40
    bar_height = 30
    bar_x = box_margin + 20
    bar_y = frame_h//2 + 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
    fill_width = int(bar_width * progress)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), (0, 255, 0), -1)
    percent = int(progress * 100)
    cv2.putText(frame, f"{percent}%", 
               (bar_x + bar_width//2 - 20, bar_y + bar_height//2 + 5), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    return frame

print("Starting eye-controlled OSU...")
print("Keep your head still during calibration.")
print("Controls:")
print("- Move eyes to control cursor")
print("- Press SPACEBAR to hit circles")
print("- Close both eyes for 1 second to quit")
print("- Press 'q' to quit")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        current_time = time.time()
        if game_active:
            if len([o for o in game_objects if not o[3]]) < MAX_CIRCLES and current_time - last_spawn_time > spawn_interval:
                spawn_game_object()
                last_spawn_time = current_time
            game_objects = cleanup_game_objects()
            valid_objects = []
            for obj in game_objects:
                still_valid = draw_circle_object(frame, obj)
                if still_valid:
                    valid_objects.append(obj)
            game_objects = valid_objects
            draw_feedback_messages(frame)
            cv2.line(frame, (cursor_x-15, cursor_y), (cursor_x+15, cursor_y), (0, 255, 255), 2)
            cv2.line(frame, (cursor_x, cursor_y-15), (cursor_x, cursor_y+15), (0, 255, 255), 2)
            overlay = frame.copy()
            box_x1, box_y1 = 5, 5
            box_x2, box_y2 = 220, 75
            cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            cv2.putText(frame, f"Score: {score}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Combo: {combo}x", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0].landmark
            left_ear = calculate_eye_aspect_ratio(face_landmarks, LEFT_EYE)
            right_ear = calculate_eye_aspect_ratio(face_landmarks, RIGHT_EYE)
            BLINK_THRESHOLD = 0.2
            both_eyes_closed = left_ear < BLINK_THRESHOLD and right_ear < BLINK_THRESHOLD
            if both_eyes_closed:
                both_eyes_closed_frames += 1
                if game_active:
                    cv2.putText(frame, "BOTH EYES CLOSED", (frame_w//2-100, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                both_eyes_closed_frames = 0
            if both_eyes_closed_frames > 15:
                print("Eyes closed - exiting program")
                break
            left_iris_center = get_iris_center(face_landmarks, LEFT_IRIS)
            right_iris_center = get_iris_center(face_landmarks, RIGHT_IRIS)
            iris_x = (left_iris_center[0] + right_iris_center[0]) / 2
            iris_y = (left_iris_center[1] + right_iris_center[1]) / 2
            if calibration_frames < CALIBRATION_FRAMES:
                center_x += iris_x
                center_y += iris_y
                calibration_frames += 1
                calibration_progress = calibration_frames / CALIBRATION_FRAMES
                frame = draw_calibration_message(frame, calibration_progress)
                if calibration_frames == CALIBRATION_FRAMES:
                    center_x /= CALIBRATION_FRAMES
                    center_y /= CALIBRATION_FRAMES
                    print("Calibration complete - eye center position established")
                    game_active = True
            else:
                x_offset = (iris_x - center_x) * EYE_MOVEMENT_MULTIPLIER
                y_offset = (iris_y - center_y) * EYE_MOVEMENT_MULTIPLIER
                target_x = np.clip(frame_w // 2 + x_offset * frame_w, 0, frame_w - 1)
                target_y = np.clip(frame_h // 2 + y_offset * frame_h, 0, frame_h - 1)
                cursor_x = int(cursor_x * SMOOTHING_FACTOR + target_x * (1 - SMOOTHING_FACTOR))
                cursor_y = int(cursor_y * SMOOTHING_FACTOR + target_y * (1 - SMOOTHING_FACTOR))
        if not game_active and calibration_frames == 0:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame_w, frame_h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, "EYE-CONTROLLED OSU", 
                       (frame_w//2 - 200, frame_h//2 - 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            cv2.putText(frame, "Press any key to start calibration", 
                       (frame_w//2 - 150, frame_h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Keep your head still during calibration", 
                       (frame_w//2 - 150, frame_h//2 + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow('Eye Controlled OSU', frame)
        key = cv2.waitKey(1) & 0xFF
        if not game_active and calibration_frames == 0 and key != 255:
            calibration_frames = 1
            print("Starting calibration...")
        if game_active and key == CLICK_KEY:
            current_time = time.time()
            if current_time - last_click_time > CLICK_COOLDOWN:
                hit_any, hit_quality, hit_index = check_hit(cursor_x, cursor_y)
                last_click_time = current_time
        if key == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    print(f"Game over! Final score: {score}")