import threading
from datetime import datetime
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

COSINE_THRESHOLD = 0.5

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://testfux-f7e98-default-rtdb.asia-southeast1.firebasedatabase.app/",
})

spreadsheet_name = "Face_Recognition_Log"
spreadsheet = ezsheets.createSpreadsheet(spreadsheet_name)
sh = spreadsheet[0]
sh[1, 1] = 'Name'
sh[2, 1] = 'Attendance Time'

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

def log_attendance_to_sheet(sheet, name):
    with sheet_lock:
        next_column = find_next_empty_column(sheet)
        sheet[1, next_column] = name
        sheet[2, next_column] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def update_human_attendance(user_id, human_name):
    ref = db.reference(f'human/{user_id}')
    human_data = ref.get()

    if human_data:
        last_attendance_time = human_data.get('human_last_attendance_time', "0001-01-01 01:01:01")
        datetime_last_attendance = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S")

        seconds_elapsed = (datetime.now() - datetime_last_attendance).total_seconds()
        print(f"Seconds since last attendance: {seconds_elapsed}")

        if seconds_elapsed > 30: 
            total_attendance = human_data.get('human_total_attendance', 0) + 1
            ref.update({
                'human_total_attendance': total_attendance,
                'human_last_attendance_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            print(f"Updated attendance for {user_id}: {total_attendance}")
            
            log_attendance_to_sheet(sh, human_name)
        else:
            print(f"Attendance update skipped for {user_id}, too soon after the last update.")
    else:
        print(f"No data found for user {user_id}")

def update_human_attendance_async(user_id, human_name):
    threading.Thread(target=update_human_attendance, args=(user_id, human_name)).start()

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
        start_hand = time.time()
        result, image = capture.read()
        if result is False:
            cv2.waitKey(0)
            break

        image = cv2.flip(image, 1)

        features, faces = recognize_face(image, face_detector, face_recognizer)
        if faces is None:
            continue

        for idx, (face, feature) in enumerate(zip(faces, features)):
            result, user = match(face_recognizer, feature, dictionary)
            box = list(map(int, face[:4]))
            color = (0, 255, 0) if result else (0, 0, 255)
            thickness = 2
            cv2.rectangle(image, box, color, thickness, cv2.LINE_AA)

            id_name, score = user if result else (f"unknown_{idx}", 0.0)

            if result:
                human_name = get_human_name_from_cache(id_name)
                update_human_attendance_async(id_name, human_name)
            else:
                human_name = id_name

            text = "{0} ({1:.2f})".format(human_name, score)
            position = (box[0], box[1] - 10)
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.6
            cv2.putText(image, text, position, font, scale,
                        color, thickness, cv2.LINE_AA)

        fps, image = fpsReader.update(image, pos=(20, 50),
                                      bgColor=(255, 255, 255),
                                      textColor=(0, 0, 0),
                                      scale=1, thickness=1, alpha=0)

        cv2.imshow("face recognition", image)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        end_hand = time.time()
        print(f'speed of a loop = {end_hand - start_hand} means {1/(end_hand - start_hand)} frames per second')

    capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
