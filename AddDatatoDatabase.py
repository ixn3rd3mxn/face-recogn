#this is AddDatatoDatabase.py

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL':"https://faceattendancerealtime-58333-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

ref = db.reference('Students')

data = {
    "people001":
        {
            "name": "Som Slash",
            "total_attendance": 0,
            "last_attendance_time": "1000-01-01 10:10:10"
        },
    "people002":
        {
            "name": "Lee Tohde",
            "total_attendance": 0,
            "last_attendance_time": "1000-01-01 10:10:10"
        },
    "people003":
        {
            "name": "Wa Todenk",
            "total_attendance": 0,
            "last_attendance_time": "1000-01-01 10:10:10"
        },
}

for key, value in data.items():
    ref.child(key).set(value)