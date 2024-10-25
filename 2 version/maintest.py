import threading
from datetime import datetime , timedelta
import os
import sys
import glob
import time
import cv2
import ezsheets
from tqdm import tqdm
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np

COSINE_THRESHOLD = 0.5

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://testfux-f7e98-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "testfux-f7e98.appspot.com"
})

def generate_sheet_name():
    """Generate a sheet name based on the current time."""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    date_str = now.strftime("%d-%m-%Y")

    # Check if the system is running between 00:01 and 05:59:59
    if (hour == 0 and (minute > 0 or second > 0)) or (1 <= hour < 6):
        print("System cannot run between 00:00:01 and 05:59:59.")
        sys.exit()

    # Determine the shift based on the current time
    if 6 <= hour < 12 or (hour == 11 and minute == 59 and second == 59):
        shift = "Morning-and-Noon-shift"
    elif 12 <= hour < 18 or (hour == 17 and minute == 59 and second == 59):
        shift = "Afternoon-and-Evening-shift"
    elif 18 <= hour <= 23:
        shift = "Night-shift"

    # Format the sheet name as hh-mm_dd-mm-yyyy_shift
    sheet_name = f"{hour:02d}-{minute:02d}_{date_str}_{shift}"
    return sheet_name

spreadsheet_name = generate_sheet_name()
spreadsheet = ezsheets.createSpreadsheet(spreadsheet_name)
sh = spreadsheet[0]
sh[1, 1] = 'Name'
sh[2, 1] = 'Attendance Time'
sh[3, 1] = 'punctual_attendance'
sh[4, 1] = 'late_attendance'
sh[5, 1] = 'finish_attendance'

human_data_cache = {}
sheet_lock = threading.Lock()

def load_human_data_from_firebase():
    global human_data_cache
    ref = db.reference('human')
    human_data_cache = ref.get()

def get_human_name_from_cache(user_id):
    if human_data_cache and user_id in human_data_cache:
        return human_data_cache[user_id].get('human_name', 'Unknown')
    return 'Unknown'

def find_next_empty_column(sheet):
    for column_num in range(1, sheet.rowCount):
        if sheet.getRow(column_num)[0] == '':
            return column_num
    return sheet.rowCount + 1

def is_name_in_sheet(sheet, name):
    for row in sheet.getRows():
        if row[0] == name:
            return True
    return False

def get_last_attendance_time_from_sheet(sheet, name):
    rows = sheet.getRows()
    for row in rows:
        if row[0] == name:
            return row[1]
    return 'not.your.time'

def log_attendance_to_sheet(sheet, name, punctual_attendance, late_attendance, finish_attendance):
    with sheet_lock:
        if not is_name_in_sheet(sheet, name):
            next_column = find_next_empty_column(sheet)
            sheet[1, next_column] = name
            sheet[2, next_column] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet[3, next_column] = punctual_attendance
            sheet[4, next_column] = late_attendance
            sheet[5, next_column] = finish_attendance
        else:
            print(f"{name} already logged, skipping...")

def update_human_attendance(user_id, human_name):
    ref = db.reference(f'human/{user_id}')
    human_data = ref.get()

    with sheet_lock:
        if is_name_in_sheet(sh, human_name):
            print(f"Name {human_name} already exists in Google Sheets and Firebase, skipping update.")
            return

    if human_data:
        last_attendance_time = human_data.get('human_last_attendance_time', "0001-01-01 01:01:01")
        datetime_last_attendance = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S")

        seconds_elapsed = (datetime.now() - datetime_last_attendance).total_seconds()
        print(f"Seconds since last attendance: {seconds_elapsed}")

        if seconds_elapsed > 1:
            # Calculate attendance status
            current_time = datetime.now().time()
            enter_work = human_data.get('Enter_work', 8)
            leave_work = human_data.get('Leave_work', 17)

            punctual_attendance, late_attendance, finish_attendance = calculate_attendance_status(current_time, enter_work, leave_work)
            
            # Only update attendance if at least one of the statuses is set to 1
            if punctual_attendance == 1 or late_attendance == 1 or finish_attendance == 1:
                # Update total attendance and last attendance time
                total_attendance = human_data.get('human_total_attendance', 0) + 1
                ref.update({
                    'human_total_attendance': total_attendance,
                    'human_last_attendance_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"Updated attendance for {user_id}: {total_attendance}")

                # Update Firebase based on attendance status
                if punctual_attendance == 1:
                    ref.update({'punctual_attendance': human_data.get('punctual_attendance', 0) + 1})
                if late_attendance == 1:
                    ref.update({'late_attendance': human_data.get('late_attendance', 0) + 1})
                if finish_attendance == 1:
                    ref.update({'finish_attendance': human_data.get('finish_attendance', 0) + 1})

                # Log to the sheet
                log_attendance_to_sheet(sh, human_name, punctual_attendance, late_attendance, finish_attendance)
            else:
                # Set human_last_attendance_time to "Not your work time"
                print(f"No valid attendance status for {user_id}, skipping update.")
        else:
            print(f"Attendance update skipped for {user_id}, too soon after the last update.")
    else:
        print(f"No data found for user {user_id}")

def update_human_attendance_async(user_id, human_name):
    threading.Thread(target=update_human_attendance, args=(user_id, human_name)).start()

def display_detected_images(image, detected_faces):
    pos_x_start = 10  # Initial x position for the first image
    pos_y = image.shape[0] - 150  # Fixed y position for all images
    idx = 0  # Counter for valid images

    for user_id, human_name, _ in detected_faces:  # Only unpack user_id and human_name, ignore last_attendance_time here
        if user_id:  # Only display image if user_id is available (ignore unknown faces)
            img_path = f'data/images/{user_id}.png'  # Image path for the detected user
            if os.path.exists(img_path):
                detected_image = cv2.imread(img_path)
                detected_image = cv2.resize(detected_image, (150, 150))  # Resize the image to fit

                pos_x = pos_x_start + idx * 160  # Offset each image by 160px to the right
                image[pos_y:pos_y + 150, pos_x:pos_x + 150] = detected_image  # Place the image on the frame
                idx += 1  # Increment counter only for known faces

    return image

def display_detected_names(image, detected_faces):
    """
    Display the names and attendance times of the detected faces below the images 
    with a semi-transparent black background. Skip displaying if the name is "unknown".
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    color = (255, 255, 255)  # White text for the name
    thickness = 2
    alpha = 0.5  # Transparency factor
    pos_x_start = 10  # Initial x position for the first name
    pos_y = image.shape[0] - 10  # Position just below the image area
    idx = 0  # Counter for valid names

    overlay = image.copy()  # Create an overlay
    output = image.copy()  # Create the final output image

    for user_id, human_name, human_last_attendance_time in detected_faces:  # Include attendance time here
        # Skip displaying if the human_name is "unknown"
        if "unknown" in human_name:
            continue

        pos_x = pos_x_start + idx * 160  # Offset each name by 160px to the right

        # Extract only the time part (hh:mm:ss) from the attendance timestamp
        time_only = human_last_attendance_time.split(" ")[1] if " " in human_last_attendance_time else human_last_attendance_time

        # Calculate text size for the name
        name_text_size = cv2.getTextSize(human_name, font, scale, thickness)[0]
        name_text_width = name_text_size[0]
        name_text_height = name_text_size[1]

        # Calculate text size for the attendance time
        attendance_text_size = cv2.getTextSize(time_only, font, scale, thickness)[0]
        attendance_text_width = attendance_text_size[0]
        attendance_text_height = attendance_text_size[1]

        # Calculate the widest text for the background rectangle width
        max_text_width = max(name_text_width, attendance_text_width)

        # Calculate the total height (name + attendance time)
        total_height = name_text_height + attendance_text_height + 15

        # Create the black background rectangle on the overlay (semi-transparent)
        cv2.rectangle(overlay, 
                      (pos_x, pos_y - total_height - 5), 
                      (pos_x + max_text_width + 10, pos_y + 5), 
                      (0, 0, 0), -1)

        # Now apply the semi-transparent overlay using the alpha factor
        cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)

        # Draw the name on the first line on the final output
        cv2.putText(output, f"{human_name}", 
                    (pos_x + 5, pos_y - attendance_text_height - 5), 
                    font, scale, color, thickness, cv2.LINE_AA)

        # Draw the attendance time (filtered to hh:mm:ss) on the second line
        cv2.putText(output, f"{time_only}", 
                    (pos_x + 5, pos_y), 
                    font, scale, color, thickness, cv2.LINE_AA)

        idx += 1  # Increment counter only for known faces

    return output

def download_images_from_storage(bucket, download_path='data/images'):
    """Download all images from Firebase Storage to a local directory."""
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    blobs = bucket.list_blobs()
    for blob in blobs:
        if blob.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            local_file_path = os.path.join(download_path, os.path.basename(blob.name))
            blob.download_to_filename(local_file_path)
            print(f"Downloaded {blob.name} to {local_file_path}")

def cleanup_local_images(download_path='data/images'):
    """Delete all images in the local directory."""
    files = glob.glob(os.path.join(download_path, '*'))
    for file in files:
        os.remove(file)
    print(f"Deleted all images in {download_path}")

def calculate_attendance_status(current_time, enter_work, leave_work):
    punctual_attendance = 0
    late_attendance = 0
    finish_attendance = 0

    # Convert times to datetime objects for comparison
    enter_time = datetime.strptime(f"{enter_work}:00:00", "%H:%M:%S").time()
    leave_time = datetime.strptime(f"{leave_work}:00:00", "%H:%M:%S").time()

    # Adjust for the range being 0 - 23
    leave_plus_4 = (leave_work + 4) % 24
    
    if enter_time > current_time >= (datetime.combine(datetime.today(), enter_time) - timedelta(hours=1)).time():
        # If current time is within 1 hour before Enter_work
        punctual_attendance = 1
    elif enter_time <= current_time < leave_time:
        # If current time is after Enter_work but before Leave_work
        late_attendance = 1
    elif leave_time <= current_time < datetime.strptime(f"{leave_plus_4}:00:00", "%H:%M:%S").time():
        # If current time is after Leave_work but within 4 hours
        finish_attendance = 1

    return punctual_attendance, late_attendance, finish_attendance

class FPS:
    def __init__(self, avgCount=30):
        self.pTime = time.time()
        self.frameTimes = []
        self.avgCount = avgCount

    def update(self, img=None, pos=(20, 50), bgColor=(255, 255, 255),
               textColor=(0, 0, 0), scale=1, thickness=1, alpha=0):
        cTime = time.time()
        frameTime = cTime - self.pTime
        self.frameTimes.append(frameTime)
        self.pTime = cTime

        if len(self.frameTimes) > self.avgCount:
            self.frameTimes.pop(0)

        avgFrameTime = sum(self.frameTimes) / len(self.frameTimes)
        fps = 1 / avgFrameTime

        if img is not None:
            text = f'FPS: {int(fps)}'
            font = cv2.FONT_HERSHEY_SIMPLEX
            textSize = cv2.getTextSize(text, font, scale, thickness)[0]
            x, y = pos
            w, h = textSize[0] + 20, textSize[1] + 20
            overlay = img.copy()
            output = img.copy()

            cv2.rectangle(overlay, (x, y - h), (x + w, y), bgColor, -1)
            cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)
            cv2.putText(output, text, (x + 10, y - 5), font, scale, textColor, thickness, cv2.LINE_AA)

            return fps, output
        return fps, img

def match(recognizer, feature1, dictionary):
    max_score = 0.0
    sim_user_id = ""
    for user_id, feature2 in zip(dictionary.keys(), dictionary.values()):
        score = recognizer.match(
            feature1, feature2, cv2.FaceRecognizerSF_FR_COSINE)
        if score >= max_score:
            max_score = score
            sim_user_id = user_id
    if max_score < COSINE_THRESHOLD:
        return False, ("", 0.0)
    return True, (sim_user_id, max_score)

def recognize_face(image, face_detector, face_recognizer, file_name=None):
    channels = 1 if len(image.shape) == 2 else image.shape[2]
    if channels == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if channels == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    if image.shape[0] > 1000:
        image = cv2.resize(image, (0, 0),
                           fx=500 / image.shape[0], fy=500 / image.shape[0])

    height, width, _ = image.shape
    face_detector.setInputSize((width, height))
    try:
        dts = time.time()
        _, faces = face_detector.detect(image)
        if file_name is not None:
            assert len(faces) > 0, f'the file {file_name} has no face'

        faces = faces if faces is not None else []
        features = []
        print(f'time detection  = {time.time() - dts}')
        for face in faces:
            rts = time.time()

            aligned_face = face_recognizer.alignCrop(image, face)
            feat = face_recognizer.feature(aligned_face)
            print(f'time recognition  = {time.time() - rts}')

            features.append(feat)
        return features, faces
    except Exception as e:
        print(e)
        print(file_name)
        return None, None

def main():
    bucket = storage.bucket()
    download_path = 'data/images'
    download_images_from_storage(bucket, download_path)

    load_human_data_from_firebase()

    directory = 'data'
    weights = os.path.join(directory, "models", "face_detection_yunet_2023mar.onnx")
    face_detector = cv2.FaceDetectorYN_create(weights, "", (0, 0))
    face_detector.setScoreThreshold(0.87)

    weights = os.path.join(directory, "models", "face_recognizer_fast.onnx")
    face_recognizer = cv2.FaceRecognizerSF_create(weights, "")

    dictionary = {}
    types = ('*.jpg', '*.png', '*.jpeg', '*.JPG', '*.PNG', '*.JPEG')
    files = []
    for a_type in types:
        files.extend(glob.glob(os.path.join(directory, 'images', a_type)))

    files = list(set(files))

    for file in tqdm(files):
        image = cv2.imread(file)
        feats, faces = recognize_face(image, face_detector, face_recognizer, file)
        if faces is None:
            continue
        user_id = os.path.splitext(os.path.basename(file))[0]
        dictionary[user_id] = feats[0]

    print(f'there are {len(dictionary)} ids')
    fpsReader = FPS(avgCount=30)
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FPS, 30)
    if not capture.isOpened():
        sys.exit()

    while True:
        result, image = capture.read()
        if result is False:
            cv2.waitKey(0)
            break

        image = cv2.flip(image, 1)

        features, faces = recognize_face(image, face_detector, face_recognizer)
        if faces is None:
            continue

        detected_faces = []  # Store detected face info as tuples (user_id, human_name, last_attendance_time)

        for idx, (face, feature) in enumerate(zip(faces, features)):
            result, user = match(face_recognizer, feature, dictionary)
            box = list(map(int, face[:4]))

            if result:
                user_id = user[0]  # This is the ID like '001'
                human_name = get_human_name_from_cache(user_id)
                human_last_attendance_time = get_last_attendance_time_from_sheet(sh, human_name)  # Pull attendance time from sheet
                detected_faces.append((user_id, human_name, human_last_attendance_time))  # Store tuple (user_id, human_name, attendance_time)

                if is_name_in_sheet(sh, human_name):
                    color = (255, 0, 0)  # Blue for already logged faces
                else:
                    color = (0, 255, 0)  # Green for new faces

                update_human_attendance_async(user_id, human_name)
            else:
                human_name = f"unknown_{idx}"
                color = (0, 0, 255)  # Red for unknown faces
                detected_faces.append((None, human_name, ""))  # Store just the name for unknown faces

            # Draw rectangle around face and display name
            thickness = 2
            cv2.rectangle(image, box, color, thickness, cv2.LINE_AA)

            text = "{0} ({1:.2f})".format(human_name, user[1])
            position = (box[0], box[1] - 10)
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.6
            cv2.putText(image, text, position, font, scale, color, thickness, cv2.LINE_AA)

        # Display the pre-existing images and names at the bottom-left
        image = display_detected_images(image, detected_faces)
        image = display_detected_names(image, detected_faces)

        # Display FPS and show window
        fps, image = fpsReader.update(image)
        cv2.imshow("face recognition", image)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    capture.release()
    cv2.destroyAllWindows()
    cleanup_local_images(download_path)

if __name__ == '__main__':
    main()