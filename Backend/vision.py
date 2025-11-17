import logging
import cv2
import math
import threading
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import sys

try:
    import mediapipe as mp  # type: ignore[import-not-found]
except ImportError as _err:
    mp = None
    _MEDIAPIPE_IMPORT_ERROR = _err

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.TextToSpeech import TextToSpeech


logger = logging.getLogger(__name__)


TARGET_RESOLUTION = (960, 540)
HUD_TINT = (20, 40, 60)

shared_state = {
    "hud_color": (0, 255, 255),
    "manual_status": None,
    "running": True,
}


def _draw_hud_overlay(frame, scan_phase: float, hud_color: Tuple[int, int, int]) -> None:
    height, width = frame.shape[:2]
    cx, cy = width // 2, height // 2

    cv2.line(frame, (cx - 60, cy), (cx - 10, cy), hud_color, 1)
    cv2.line(frame, (cx + 10, cy), (cx + 60, cy), hud_color, 1)
    cv2.line(frame, (cx, cy - 60), (cx, cy - 10), hud_color, 1)
    cv2.line(frame, (cx, cy + 10), (cx, cy + 60), hud_color, 1)
    cv2.circle(frame, (cx, cy), 70, hud_color, 1, lineType=cv2.LINE_AA)

    sweep_radius = min(cx, cy) - 40
    angle = (scan_phase % 360) * math.pi / 180
    sweep_x = int(cx + sweep_radius * math.cos(angle))
    sweep_y = int(cy + sweep_radius * math.sin(angle))
    cv2.line(frame, (cx, cy), (sweep_x, sweep_y), hud_color, 1)

    margin = 25
    cv2.rectangle(frame, (margin, margin), (width - margin, height - margin), hud_color, 1)
    cv2.putText(
        frame,
        "M.A.H.I. VISION ONLINE",
        (margin + 10, margin + 25),
        cv2.FONT_HERSHEY_DUPLEX,
        0.6,
        hud_color,
        1,
        cv2.LINE_AA,
    )


def _draw_eye_pointers(frame, eye_points: List[Tuple[int, int]], hud_color: Tuple[int, int, int]) -> None:
    for (ex, ey) in eye_points:
        cv2.circle(frame, (ex, ey), 5, hud_color, -1)
        cv2.circle(frame, (ex, ey), 10, hud_color, 1)


def _annotate_status(frame, status: str, fps: float, hud_color: Tuple[int, int, int]) -> None:
    height = frame.shape[0]
    info_color = (255, 255, 255)
    display_status = shared_state.get("manual_status") or status
    cv2.putText(
        frame,
        f"STATUS: {display_status}",
        (20, height - 35),
        cv2.FONT_HERSHEY_DUPLEX,
        0.6,
        info_color,
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, height - 10),
        cv2.FONT_HERSHEY_DUPLEX,
        0.55,
        info_color,
        1,
        cv2.LINE_AA,
    )


def command_listener() -> None:
    logger.info("--- M.A.H.I. Command Prompt ---")
    logger.info("Type 'help' for available commands.")

    while shared_state["running"]:
        try:
            prompt = input("M.A.H.I. > ").strip()
        except (EOFError, KeyboardInterrupt):
            shared_state["running"] = False
            break

        if not prompt:
            continue

        parts = prompt.split()
        command = parts[0].lower()

        if command == "help":
            logger.info("Commands:")
            logger.info("  say <message>")
            logger.info("  color <r> <g> <b>")
            logger.info("  status <message>")
            logger.info("  reset status")
            logger.info("  exit / quit")
            continue

        if command == "say":
            message = prompt[len("say") :].strip()
            if message:
                threading.Thread(target=TextToSpeech, args=(message,), daemon=True).start()
            continue

        if command == "color":
            if len(parts) == 4:
                try:
                    r, g, b = int(parts[1]), int(parts[2]), int(parts[3])
                    shared_state["hud_color"] = (b, g, r)
                except ValueError:
                    logger.warning("Invalid color values supplied for HUD color change.")
            else:
                logger.info("Usage: color <r> <g> <b>")
            continue

        if command == "status":
            message = prompt[len("status") :].strip()
            if message:
                shared_state["manual_status"] = message.upper()
            else:
                logger.info("Usage: status <message>")
            continue

        if command == "reset" and len(parts) > 1 and parts[1].lower() == "status":
            shared_state["manual_status"] = None
            continue

        if command in {"exit", "quit"}:
            shared_state["running"] = False
            break

        logger.info("Unknown command received: '%s'.", command)

    logger.info("Command listener shutting down.")


def start_vision() -> None:
    cmd_thread = threading.Thread(target=command_listener, daemon=True)
    cmd_thread.start()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error("Could not open webcam for vision module.")
        shared_state["running"] = False
        return

    face_mesh = None
    eye_cascade = None

    if mp is not None:
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    else:
        logger.warning("MediaPipe unavailable; switching to OpenCV Haar cascade for eye detection.")
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_eye.xml"
        eye_cascade = cv2.CascadeClassifier(str(cascade_path))
        if eye_cascade.empty():
            logger.error("Failed to load Haar cascade for eye detection from %s.", cascade_path)
            shared_state["running"] = False
            cap.release()
            return

    prev_time = time.time()
    scan_phase = 0.0

    while shared_state["running"]:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, TARGET_RESOLUTION)
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()

        tint_layer = np.full_like(display_frame, HUD_TINT)
        display_frame = cv2.addWeighted(display_frame, 0.8, tint_layer, 0.2, 0)

        eye_points: List[Tuple[int, int]] = []
        status_text = "AWAITING USER"

        if face_mesh is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            if results.multi_face_landmarks:
                status_text = "USER DETECTED"
                landmarks = results.multi_face_landmarks[0].landmark
                height, width = frame.shape[:2]
                left_idx, right_idx = 473, 468
                left_pt = landmarks[left_idx]
                right_pt = landmarks[right_idx]
                eye_points.append((int(left_pt.x * width), int(left_pt.y * height)))
                eye_points.append((int(right_pt.x * width), int(right_pt.y * height)))
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
            if len(eyes) > 0:
                status_text = "USER DETECTED"
                eyes_sorted = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
                for (ex, ey, ew, eh) in eyes_sorted:
                    eye_points.append((ex + ew // 2, ey + eh // 2))

        if eye_points:
            _draw_eye_pointers(display_frame, eye_points, shared_state["hud_color"])

        current_time = time.time()
        fps = 1.0 / (current_time - prev_time) if current_time != prev_time else 0.0
        prev_time = current_time

        scan_phase += 90 * (1 / max(fps, 1e-3))
        _draw_hud_overlay(display_frame, scan_phase, shared_state["hud_color"])
        _annotate_status(display_frame, status_text, fps, shared_state["hud_color"])

        cv2.imshow("JARVIS Vision", display_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            shared_state["running"] = False

    cap.release()
    cv2.destroyAllWindows()
    logger.info("Vision system offline.")
    if face_mesh is not None:
        face_mesh.close()


if __name__ == "__main__":
    start_vision()