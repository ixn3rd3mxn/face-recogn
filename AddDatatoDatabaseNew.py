#this is AddDatatoDatabase.py

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL':"https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

ref = db.reference('Students')

# Constant values for total_attendance and last_attendance_time
total_attendance = 0
last_attendance_time = "0001-01-01 01:01:01"

# Function to add a new student to the database
def add_student():
    student_id = input("Enter student ID: ")
    name = input("Enter student name: ")

    student_data = {
        "name": name,
        "total_attendance": total_attendance,
        "last_attendance_time": last_attendance_time
    }

    ref.child(student_id).set(student_data)
    print(f"Student {name} with ID {student_id} added to the database.")

# Loop to add multiple students
while True:
    add_student()
    another = input("Do you want to add another student? (yes/no): ")
    if another.lower() != 'yes':
        break

print("Finished adding students.")