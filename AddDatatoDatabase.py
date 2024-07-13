#this is AddDatatoDatabase.py

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL':"https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

ref = db.reference('Students')

data = {
    "001":
        {
            "name": "Som Slash",
            "total_attendance": 7,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "002":
        {
            "name": "Lee Tohde",
            "total_attendance": 7,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "003":
        {
            "name": "Wa Todenk",
            "total_attendance": 7,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
}

for key, value in data.items():
    ref.child(key).set(value)