import cv2
from mtcnn import MTCNN
import os
import face_recognition
import pickle
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

def detect_and_save_faces(folder_name):
    output_dir = os.path.join('Images', folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(0)
    count = 0  # Counter for the saved cropped faces
    margin = 20  # Define the margin (in pixels)
    max_images = 30  # Maximum number of images to save

    while count < max_images:
        ret, frame = cap.read()
        faces = detector.detect_faces(frame)

        for face in faces:
            if count >= max_images:
                break
            x, y, w, h = face['box']
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = w + 2 * margin
            h = h + 2 * margin
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            face_crop = frame[y:y + h, x:x + w]
            face_filename = os.path.join(output_dir, f'{folder_name}_{count}.png')
            cv2.imwrite(face_filename, face_crop)
            count += 1

        cv2.imshow('Webcam Face Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Encode and upload images to Firebase Storage
    encode_and_upload_all_images()

def encode_and_upload_all_images():
    folder_path = 'Images'
    encode_dict = {}

    path_list = os.listdir(folder_path)
    for path in path_list:
        student_folder = os.path.join(folder_path, path)
        if os.path.isdir(student_folder):
            img_list = []
            for filename in os.listdir(student_folder):
                img_path = os.path.join(student_folder, filename)
                img = cv2.imread(img_path)
                if img is not None:
                    img_list.append(img)
                    file_name = f'{folder_path}/{path}/{filename}'
                    bucket = storage.bucket()
                    blob = bucket.blob(file_name)
                    blob.upload_from_filename(file_name)
                    print(f'Uploaded {file_name} to Firebase Storage')

            if img_list:
                encode_dict[path] = find_encodings(img_list)

    with open("EncodeFile.p", 'wb') as file:
        pickle.dump(encode_dict, file)

    print("Encoding Complete and File Saved")

def find_encodings(images_list):
    encode_list = []
    for img in images_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encode = encodings[0]
            encode_list.append(encode)
    return encode_list

def main():
    while True:
        print("\nMenu:")
        print("1. Show available folders")
        print("2. Create folder and detect faces")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            bucket_name = "faceplus-1b3e4.appspot.com"
            folders = list_subfolders_in_images(bucket_name)
            print("Existing folders in 'Images' folder in Firebase Storage:")
            for folder in folders:
                print(folder)
        elif choice == '2':
            folder_name = input("Enter the folder name: ")
            detect_and_save_faces(folder_name)
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
