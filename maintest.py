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

start_time = time.time()

while True:
    elapsed_time = int(time.time() - start_time)
    countdown_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    print(f"Countdown: {countdown_str}", end="\r")  # Print the countdown in-place

    # Stop the countdown after 1 second or press any key to stop it manually.
    time.sleep(1) 
    if elapsed_time >= 1:
        break

print("\nLoading Encode File ...")

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

# Stop the countdown and print the elapsed time
end_time = time.time()
elapsed_time = int(end_time - start_time)
countdown_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
print(f"Elapsed time: {countdown_str}")
print(studentIds)
print("Encode File Loaded")
