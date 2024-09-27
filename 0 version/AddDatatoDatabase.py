import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "PUT UR LINK STORAGE FIREBASE" , # ex : "https://xxx-xxx-default-xxx.asia-southeast1.firebasedatabase.app/"
    'storageBucket': "PUT UR LINK STORAGE FIREBASE" # ex : "xxx-xxx.appspot.com"
})

ref = db.reference('Students')

data = {
    "001":
        {
            "name": "Som Slash",
            "total_attendance": 7,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
}

for key, value in data.items():
    ref.child(key).set(value)