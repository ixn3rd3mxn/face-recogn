import cv2
from mtcnn import MTCNN
import os

# Initialize MTCNN face detector
detector = MTCNN()

# Get user input for the folder name
folder_name = input("Enter the folder name: ")

# Create the directory to save cropped faces if it doesn't exist
output_dir = os.path.join('Images', folder_name)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Initialize the webcam
cap = cv2.VideoCapture(0)

count = 0  # Counter for the saved cropped faces

# Define the margin (in pixels)
margin = 20

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # Detect faces in the frame
    faces = detector.detect_faces(frame)

    # Draw rectangles around the faces and crop them
    for face in faces:
        x, y, w, h = face['box']
        
        # Add margin to the bounding box coordinates
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = w + 2 * margin
        h = h + 2 * margin
        
        # Draw a rectangle around the face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Crop the face from the frame
        face_crop = frame[y:y + h, x:x + w]
        
        # Save the cropped face
        face_filename = os.path.join(output_dir, f'{folder_name}_{count}.png')
        cv2.imwrite(face_filename, face_crop)
        count += 1

    # Display the resulting frame
    cv2.imshow('Webcam Face Detection', frame)
    
    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and close windows
cap.release()
cv2.destroyAllWindows()
