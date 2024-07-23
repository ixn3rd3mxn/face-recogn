#this is AddDatatoDatabase.py

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL':"https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

ref = db.reference('Students') #create table or replace this name table in database

data = {
    "001":
        {
            "name": "Esom Salaeh",
            "total_attendance": 0,
            "last_attendance_time": "0001-01-01 01:01:01"
        },
    "002":
        {
            "name": "Hanafee Useng",
            "total_attendance": 0,
            "last_attendance_time": "0001-01-01 01:01:01"
        },
    "003":
        {
            "name": "Sulkiflee Tohde",
            "total_attendance": 0,
            "last_attendance_time": "0001-01-01 01:01:01"
        },
    "004":
        {
            "name": "Dr attapon",
            "total_attendance": 0,
            "last_attendance_time": "0001-01-01 01:01:01"
        },
}

for key, value in data.items():
    ref.child(key).set(value)