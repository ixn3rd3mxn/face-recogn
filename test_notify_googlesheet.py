import ezsheets

#ezsheets.upload('Condo list.xlsx')

s = ezsheets.Spreadsheet('https://docs.google.com/spreadsheets/d/1MNhHL8TpBuiTR5VS1YPEzdyvadxEB5F_iKs4TVUkBZo/edit?gid=1143167581#gid=1143167581')
sh = s.sheets[1]

#print(s.title)
#s.title = 'Class Data'
#print(s.title)

#print(sh.columnCount, sh.rowCount)

#print(sh.get(1,1))
#sh.update(1, 1, 'asdasdadsd')
#print(sh.get(1,1))

#sh.update(1, 1, str(studentInfo['last_attendance_time']))

print (sh.get(1,1))