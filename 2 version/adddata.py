import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://testfux-f7e98-default-rtdb.asia-southeast1.firebasedatabase.app/",
})

ref = db.reference('human')

data = {
    "001":
        {
            "human_name": "esom",
            "human_total_attendance": 0,
            "human_last_attendance_time": "0001-01-01 01:01:01"
        },
    "002":
        {
            "human_name": "kid",
            "human_total_attendance": 0,
            "human_last_attendance_time": "0001-01-01 01:01:01"
        },
}

for key, value in data.items():
    ref.child(key).set(value)