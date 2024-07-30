import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

ref = db.reference('Students')

# Constant values for total_attendance and last_attendance_time
total_attendance = 0
last_attendance_time = "0001-01-01 01:01:01"

# Function to display all students in the database
def display_students():
    students = ref.get()
    if students:
        print("Current students in the database:")
        for student_id, student_data in students.items():
            print(f"ID: {student_id}, Name: {student_data['name']}, "
                  f"Total Attendance: {student_data['total_attendance']}, "
                  f"Last Attendance Time: {student_data['last_attendance_time']}")
    else:
        print("No students found in the database.")

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

# Function to delete a student from the database
def delete_student():
    student_id = input("Enter the student ID to delete: ")
    if ref.child(student_id).get():
        ref.child(student_id).delete()
        print(f"Student with ID {student_id} has been deleted.")
    else:
        print(f"No student found with ID {student_id}.")

# Main loop to show options and perform actions
while True:
    display_students()
    
    print("\nOptions:")
    print("1. Add a student")
    print("2. Delete a student")
    print("3. Exit")
    
    choice = input("Enter your choice: ")
    
    if choice == '1':
        add_student()
    elif choice == '2':
        delete_student()
    elif choice == '3':
        break
    else:
        print("Invalid choice. Please try again.")
    
    print("\nUpdated database:")

print("Finished updating students.")
