import cv2
import os
import base64

def capture_image(filename="vision_input.jpg"):
    """Captures a frame from the webcam and saves it to a file."""
    # Try multiple indices if 0 fails
    for index in [0, 1, 2]:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Wait a bit for the camera to warm up
            for _ in range(10):
                cap.read()
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(filename, frame)
                cap.release()
                return os.path.abspath(filename)
            cap.release()
    return None

def encode_image(image_path):
    """Encodes an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
