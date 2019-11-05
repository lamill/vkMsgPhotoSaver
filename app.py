import vkApi
import json
from time import sleep
import sys
import requests
import os
import asyncio

login = ''
password = ''
vk = vkApi.messages(login, password)
SLEEP_TIME = 0.3
ROOT_FOLDER = login + '_photos'

def setStatus(statusStr):
    sys.stdout.write('\r{}'.format(statusStr))
    sys.stdout.flush()

def getChats():
    print('Getting list of dialogs')
    def formUsers(ids):
        users = []
        js = vk.method('users.get', user_ids = ids)
        js = json.loads(js['payload'][1][0])

        for item in js['response']:
            user = {
                'name': item['first_name'] + ' ' + item['last_name'],
                'id': item['id']
            }
            users.append(user)
        return users

    def formGroups(ids):
        groups = []
        js = vk.method('groups.getById', group_ids = ids)
        js = json.loads(js['payload'][1][0])
        if 'response' not in js:
            print(js)
            return []
        for item in js['response']:
            group = {
                'name': item['name'],
                'id': item['id']
            }
            groups.append(group)
        return groups


    def formChats(items):
        chats = []
        users = []
        groups = []
        for item in items:
            chatType = item['conversation']['peer']['type']
            chatId = item['conversation']['peer']['id']
            
            if chatType == 'chat':
                chat = {
                    'name': item['conversation']['chat_settings']['title'],
                    'id': chatId
                }
                chats.append(chat)
            elif chatType == 'user':
                users.append(chatId)
            else:
                groups.append(chatId)
        if len(users) != 0:
            users = [str(user) for user in users]
            users = formUsers(','.join(users))
            chats.extend(users)
            sleep(SLEEP_TIME)

        if len(groups) != 0:
            groups = [str(-group) for group in groups]
            groups = formGroups(','.join(groups))
            chats.extend(groups)
            sleep(SLEEP_TIME)

        return chats
    
    cnt = 200
    js = vk.method('messages.getConversations', count = cnt, filter = 'all')
    js = json.loads(js['payload'][1][0])
    js = js['response']
    chats = formChats(js['items'])
            
    total  = js['count']
    ofst = cnt
    setStatus('{} dialogs received'.format(len(chats)))
    while(len(chats)<total):
        js = vk.method('messages.getConversations', count = cnt, filter = 'all', offset = ofst)
        js = json.loads(js['payload'][1][0])
        js = js['response']
        temp_chats = formChats(js['items'])
        chats.extend(temp_chats)
        ofst= ofst+cnt
        setStatus('{} dialogs received'.format(len(chats)))
        sleep(SLEEP_TIME)
    print('\nDone!')
    for chat in chats:
        chat['name'] = chat['name'].replace('/',' ')
    return chats

def getPhotosList(id):
    ofst = 0
    photos = []
    cnt = 200  
    print('Getting list of photos')
    while (True):
        js = vk.method('messages.getHistoryAttachments', 
        peer_id = id,
        media_type = 'photo',
        count = cnt,
        start_from = ofst 
        )
        js = json.loads(js['payload'][1][0])
        if 'response' not in js:
            print(js)
        js = js['response']

        if( len(js['items']) == 0):
            setStatus('{} photos received'.format(len(photos)))
            break

        temp_photos = [item['attachment']['photo']['sizes'][-1]['url'] for item in js['items']]
        photos.extend(temp_photos)
        setStatus('{} photos received'.format(len(photos)))
        ofst = js['next_from']
        sleep(SLEEP_TIME)
    sleep(SLEEP_TIME)
    print('\nDone!')
    return photos

def downloadPhotos(lst, dir_):
    folder = ROOT_FOLDER+'/'+dir_
    i = 0
    lst_len = len(lst)

    if dir_ not in os.listdir(ROOT_FOLDER):
        os.mkdir(os.path.normpath(folder))

    print('Downloading photos')
        
    setStatus('{} photos downloaded from {}'.format(i, lst_len))

    for url in lst:
        r = requests.get(url, allow_redirects=True)

        filename = folder+'/'+url.split('/')[-1]
        filename = os.path.normpath(filename)

        with open(filename, 'wb') as file:
            file.write(r.content)

        i+=1
        msg = '{} photos downloaded from {}'.format(i, lst_len)
        setStatus(msg)

    print('\nDone!')

if ROOT_FOLDER not in os.listdir():
    os.mkdir(ROOT_FOLDER)

ignore_list = []
with open('ignore_list', 'r') as f:
        ignore_list = [int(line.split('\n')[0]) for line in f]
        
chats = getChats()
chats = list(filter(lambda item: item['id'] not in ignore_list, chats))
lst_len = len(chats)
for num, chat in enumerate(chats):
    print('-----------------------------------------')
    print('Working with {} ({} of {})\nDialog id:{}'.format(chat['name'], num+1, lst_len,chat['id']))
    photos = getPhotosList(chat['id'])
    if len(photos) != 0:
        downloadPhotos(photos, chat['name'])


