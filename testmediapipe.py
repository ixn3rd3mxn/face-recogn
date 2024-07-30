import os
import cv2
import numpy as np

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MARGIN = 10  # pixels
ROW_SIZE = 10  # pixels
FONT_SIZE = 5
FONT_THICKNESS = 1
TEXT_COLOR = (255, 0, 0)  # red
BBOX_MARGIN = 30  # Margin around the bounding box to make it wider

# Ensure the cropped_faces directory exists
os.makedirs('cropped_faces', exist_ok=True)

def visualize(image, detection_result, confidence_threshold: float, frame_counter: int) -> np.ndarray:
    annotated_image = image.copy()
    height, width, _ = image.shape
    for detection in detection_result.detections:
        # Only visualize detections with a confidence score above the threshold
        if detection.categories[0].score < confidence_threshold:
            continue

        bbox = detection.bounding_box
        start_point = max(bbox.origin_x - BBOX_MARGIN, 0), max(bbox.origin_y - 75 - BBOX_MARGIN, 0)
        end_point = min(bbox.origin_x + bbox.width + BBOX_MARGIN, width), min(bbox.origin_y + bbox.height + BBOX_MARGIN, height)
        cv2.rectangle(annotated_image, start_point, end_point, TEXT_COLOR, 3)
        
        # Crop face and save it with margin
        crop_img = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]
        cv2.imwrite(f'cropped_faces/face_{frame_counter}.jpg', crop_img)


        category = detection.categories[0]
        category_name = category.category_name
        category_name = '' if category_name is None else category_name
        probability = round(category.score, 2)
        result_text = f"{category_name} ({probability})"
        text_location = (MARGIN + bbox.origin_x, MARGIN + ROW_SIZE + bbox.origin_y)
        cv2.putText(annotated_image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN, FONT_SIZE, TEXT_COLOR, FONT_THICKNESS)
    return annotated_image

# Define confidence threshold
CONFIDENCE_THRESHOLD = 0.7

# Create a FaceDetector object
base_options = python.BaseOptions(model_asset_path='detector.tflite')
options = vision.FaceDetectorOptions(base_options=base_options, min_detection_confidence=CONFIDENCE_THRESHOLD)
detector = vision.FaceDetector.create_from_options(options)

# Start capturing video from the webcam
cap = cv2.VideoCapture(0)  # Use 0 for the default camera

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

frame_counter = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # Convert the frame to the format expected by MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # Detect faces in the frame
    detection_result = detector.detect(image)

    # Visualize the detection results and save cropped faces
    annotated_image = visualize(frame, detection_result, CONFIDENCE_THRESHOLD, frame_counter)

    # Display the annotated image
    cv2.imshow('Webcam Face Detection', annotated_image)

    # Exit loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_counter += 1

# Release the webcam and close the window
cap.release()
cv2.destroyAllWindows()
