****************************************************

0 version folder is first version , i Make some minor tweaks from @cvzone and my Face Recognition is use lib face-recognition only

1 version folder is next version , i ve upgraded a lot of things like voice acting / using google sheets / google drive / etc and my Face Recognition is use lib face-recognition only

2 version folder recently (developing a system) and and my Face Recognition is't use lib but it use face_recognizer_fast.onnx model and YuNet model

****************************************************

What is required ?

1 . cmake , go to https://cmake.org/download/ , find Binary distributions and click download Windows x64 Installer , install now and go to tick add path

2 . visual studio , go to https://visualstudio.microsoft.com/ , find Download Visual Studio button purple and click download this , install now / in workloads go to tick desktop development with C++ and in individual components go to tick cmake tools for windows

3 . requirements.txt , pip install -r requirements.txt

4 . any pickle and json file :-
- credentials.json : get in google cloud , go enable Google Sheets API and Google Drive API , go to get Credentials
- credentials-sheets.json : same as credentials.json , Just change file name
- serviceAccountKey.json : get in firebase , go to setting in lobby and click project setting and click Service account , in Admin SDK configuration snippet go to choose python and click Generate new private key , it give file
- token.json : obtained after running main.py and AdminAIO_GUI.py
- token-drive.pickle : same as token.json
- token-sheets.pickle : same as token.json

****************************************************

Details

main.py for user
AdminAIO_GUI.py for admin

****************************************************

รายละเอียดโครงการและข้อกำหนด

โครงสร้างโฟลเดอร์เวอร์ชัน:

เวอร์ชัน 0
เป็นเวอร์ชันแรก มีการปรับแต่งเล็กน้อยจาก @cvzone
ใช้ไลบรารี face-recognition ในการจดจำใบหน้าเท่านั้น

เวอร์ชัน 1
เป็นเวอร์ชันถัดมา มีการปรับปรุงเพิ่มเติมหลายอย่าง เช่น
การเพิ่มเสียงพากย์
ใช้ Google Sheets และ Google Drive
ใช้ไลบรารี face-recognition และ mediapip ในการจดจำใบหน้าเท่านั้น

เวอร์ชัน 2 (เวอร์ชันปัจจุบัน)
กำลังพัฒนาระบบ
เลิกใช้ไลบรารี face-recognition และ mediapip แต่เปลี่ยนมาใช้โมเดล face_recognizer_fast.onnx และ YuNet ในการจดจำใบหน้า

สิ่งที่ต้องใช้ในการตั้งค่า:

CMake
ดาวน์โหลดได้จาก CMake
ไปที่หัวข้อ Binary distributions และดาวน์โหลดตัวติดตั้งสำหรับ Windows x64
ติดตั้งแล้วเลือกตัวเลือก Add to PATH

Visual Studio
ดาวน์โหลดได้จาก Visual Studio
คลิกปุ่ม Download Visual Studio สีม่วง
ระหว่างการติดตั้ง:
ในส่วน Workloads ให้เลือก Desktop Development with C++
ในส่วน Individual components ให้เลือก CMake tools for Windows

ติดตั้ง dependencies จากไฟล์ requirements.txt

ใช้คำสั่ง pip install -r requirements.txt

ไฟล์ pickle และ json ที่จำเป็น:
credentials.json:
ได้จาก Google Cloud
เปิดใช้งาน Google Sheets API และ Google Drive API
ไปที่ส่วน Credentials เพื่อสร้างไฟล์

credentials-sheets.json:
สร้างเหมือนกับ credentials.json แต่เปลี่ยนชื่อไฟล์

serviceAccountKey.json:
ได้จาก Firebase
ไปที่หน้า Settings ในหน้าโครงการ
คลิก Project settings > Service account > Admin SDK configuration snippet
เลือก Python แล้วคลิก Generate new private key เพื่อดาวน์โหลดไฟล์

token.json:
ได้มาหลังจากรัน main.py และ AdminAIO_GUI.py

token-drive.pickle:
สร้างเหมือนกับ token.json

token-sheets.pickle:
สร้างเหมือนกับ token.json

รายละเอียดเพิ่มเติม:
main.py: สำหรับผู้ใช้งานทั่วไป
AdminAIO_GUI.py: สำหรับแอดมิน
