import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import datetime
import ezsheets
import time
from gtts import gTTS

# Function to generate a sheet name based on the current date and time
def generate_sheet_name():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    if now.time() >= datetime.time(0, 0, 0) and now.time() <= datetime.time(11, 59, 59):
        time_str = 'Enter_work'
    elif now.time() >= datetime.time(12, 0, 0) and now.time() <= datetime.time(23, 59, 59):
        time_str = 'Leave_work'
    else:
        time_str = 'Other_work'

    return f"{date_str}_{time_str}"

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

import pygame

def play_greeting(name):
    text = f"Hello! , Good morning {name}."
    language = 'en'
    speech = gTTS(text=text, lang=language, slow=False)
    file_path = "greeting.mp3"
    
    # Save the speech to an mp3 file
    speech.save(file_path)
    
    try:
        # Initialize the mixer and play the audio file
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        # Wait until the music is finished playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Check every 100ms
    except Exception as e:
        print("An error occurred while trying to play the sound:", e)
    finally:
        # Stop the music and uninitialize the mixer to release the file
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        # Ensure the file is deleted
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete the file: {e}")

# Generate a new sheet title based on the current date and time
new_sheet_title = generate_sheet_name()

# Create a new spreadsheet with the dynamic name
new_spreadsheet = ezsheets.createSpreadsheet(new_sheet_title)

# Print the URL and ID of the new spreadsheet
print('New spreadsheet created:')
print('Spreadsheet ID:', new_spreadsheet.spreadsheetId)

# Use the spreadsheetId to control the new spreadsheet
s = ezsheets.Spreadsheet(new_spreadsheet.spreadsheetId)

# Access the first sheet
sh = s[0]

sh[1, 1] = 'Name'
sh[2, 1] = 'Attendance time'

from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "faceplus-1b3e4.appspot.com"
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')

folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
print(len(imgModeList))

print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')
encodeDict = pickle.load(file)
file.close()

# Flatten the dictionary to list of encodings and corresponding IDs
encodeListKnown = []
studentIds = []
for student_id, encodings in encodeDict.items():
    for encoding in encodings:
        encodeListKnown.append(encoding)
        studentIds.append(student_id)

print(studentIds)
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgStudent = []

pause_face_recognition = False
pause_start_time = 0
pause_duration = 10  # Pause face recognition for 10 seconds after each detection

while True:
    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    current_time = time.time()

    if not pause_face_recognition:
        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
    else:
        faceCurFrame = []
        if current_time - pause_start_time > pause_duration:
            pause_face_recognition = False

    if faceCurFrame and not pause_face_recognition:
        # Find the closest face
        largest_area = 0
        closest_face_index = -1
        for i, faceLoc in enumerate(faceCurFrame):
            y1, x2, y2, x1 = faceLoc
            face_area = (x2 - x1) * (y2 - y1)
            if face_area > largest_area:
                largest_area = face_area
                closest_face_index = i

        if closest_face_index != -1:
            # Proceed with recognition for the closest face
            encodeFace = encodeCurFrame[closest_face_index]
            faceLoc = faceCurFrame[closest_face_index]

            matches = face_recognition.compare_faces(encodeListKnown, encodeFace, tolerance=0.4)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            print("matches", matches)
            print("faceDis", faceDis)

            matchIndex = np.argmin(faceDis)
            print("Match Index", matchIndex)

            if matches[matchIndex] and faceDis[matchIndex] < 0.4:  # Adjusted threshold for better accuracy
                print("Known Face Detected")
                print(studentIds[matchIndex])
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]
                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1
            else:
                print("Unknown Face Detected")
                modeType = 3
                counter = 0
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if counter != 0:
            if counter == 1:
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)
                blob = bucket.get_blob(f'Images/{id}/{id}_29.png')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)
                if not is_name_in_sheet(sh, studentInfo['name']):
                    ref = db.reference(f'Students/{id}')
                    studentInfo['total_attendance'] += 1
                    ref.child('total_attendance').set(studentInfo['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                    next_column = find_next_empty_column(sh)
                    sh.update(1, next_column, str(studentInfo['name']))
                    sh.update(2, next_column, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    
                    # Play greeting for the recognized user
                    play_greeting(studentInfo['name'])

                else:
                    modeType = 3
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            if modeType != 3:
                if 10 < counter < 20:
                    modeType = 2

                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if counter <= 10:
                    cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(id), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    #imgBackground[175:175 + 216, 909:909 + 216] = imgStudent
                    #time.sleep(10)
                counter += 1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    studentInfo = []
                    imgStudent = []
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            # Start pause after processing a face
            pause_face_recognition = True
            pause_start_time = current_time
    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)