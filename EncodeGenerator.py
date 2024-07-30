import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL':"https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "faceplus-1b3e4.appspot.com"
})

# Importing student images
folderPath = 'Images'
pathList = os.listdir(folderPath)
print(pathList)
encodeDict = {}

for path in pathList:
    student_folder = os.path.join(folderPath, path)
    imgList = []
    for filename in os.listdir(student_folder):
        img = cv2.imread(os.path.join(student_folder, filename))
        imgList.append(img)

        fileName = f'{folderPath}/{path}/{filename}'
        bucket = storage.bucket()
        blob = bucket.blob(fileName)
        blob.upload_from_filename(fileName)

        print(fileName)
        print(path)

    def findEncodings(imagesList):
        encodeList = []
        for img in imagesList:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(img)
            if encodings:  # Check if any encodings are found
                encode = encodings[0]
                encodeList.append(encode)
            #else:
                #print(f"No face found in image for {path}")
                #cv2.imshow(f"No face found in {path}", img)
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()

        return encodeList

    print("Encoding Started ...")
    encodeListKnown = findEncodings(imgList)
    encodeDict[path] = encodeListKnown
    print("Encoding Complete")

print(encodeDict)

file = open("EncodeFile.p", 'wb')
pickle.dump(encodeDict, file)
file.close()
print("File Saved")
