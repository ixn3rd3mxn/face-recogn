****************************************************

0 version folder is first version , i Make some minor tweaks from @cvzone

1 version folder is next version , i ve upgraded a lot of things like voice acting / using google sheets / google drive / etc.

2 version folder recently (developing a system)

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
