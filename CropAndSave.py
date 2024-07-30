import cv2
from mtcnn import MTCNN
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "faceplus-1b3e4.appspot.com"
})

# Initialize MTCNN face detector
detector = MTCNN()

def list_subfolders_in_images(bucket_name):
    bucket = storage.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix='Images/')

    folders = set()
    for blob in blobs:
        parts = blob.name.split('/')
        if len(parts) > 2:  # Make sure it is a subfolder
            folders.add(parts[1])

    return folders

# Display existing subfolders in the 'Images' folder in Firebase Storage
bucket_name = "faceplus-1b3e4.appspot.com"
folders = list_subfolders_in_images(bucket_name)
print("Existing folders in 'Images' folder in Firebase Storage:")
for folder in folders:
    print(folder)

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
max_images = 30  # Maximum number of images to save

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # Detect faces in the frame
    faces = detector.detect_faces(frame)

    # Draw rectangles around the faces and crop them
    for face in faces:
        if count >= max_images:
            break
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
    
    # Break the loop if the maximum number of images is reached
    if count >= max_images:
        print(f"Reached the maximum of {max_images} images.")
        break
    
    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and close windows
cap.release()
cv2.destroyAllWindows()