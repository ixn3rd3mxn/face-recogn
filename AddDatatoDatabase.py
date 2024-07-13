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
            "total_attendance": 1,
            "last_attendance_time": "2024-12-12 23:59:59"
        },
    "002":
        {
            "name": "Lee Tohde",
            "total_attendance": 1,
            "last_attendance_time": "2024-12-12 23:59:59"
        },
    "003":
        {
            "name": "Wa Todenk",
            "total_attendance": 1,
            "last_attendance_time": "2024-12-12 23:59:59"
        },
}

for key, value in data.items():
    ref.child(key).set(value)