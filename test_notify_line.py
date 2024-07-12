import requests
url = 'https://notify-api.line.me/api/notify'
token = 'e8wMjCsVUS1ifwlVaQuM8x3hNzTMP6LkSaBlvPQNLDg'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token}

msg = 'ดีครับคุณฮาซานของผม'
r = requests.post(url, headers=headers, data = {'message':msg})
print (r.text)