import imaplib
from imbox import Imbox
from dateutil.parser import parse
import datetime
import os
import shutil
import schedule
import time


#Configuration
CFG_IMAP_LOGIN = os.environ.get('CFG_IMAP_LOGIN') #'%YOUR_IMAP_LOGIN%'
CFG_IMAP_PASS = os.environ.get('CFG_IMAP_PASS') #'%YOUR_IMAP_PASS%'
CFG_IMAP_HOST = os.environ.get('CFG_IMAP_HOST') #'%YOUR_IMAP_HOST%'
CFG_FOLDER_TO_WRITE = os.environ.get('CFG_FOLDER_TO_WRITE') #'%YOUR_FOLDER_TO_WRITE_NOTES%'
CFG_FOLDER_RESOURCES = os.environ.get('CFG_FOLDER_TO_WRITE') #'%YOUR_CFG_FOLDER_RESOURCES%'

def writer(folder_to_save, date, time, tags = [], note_name = "", note_text = "", attachments = [], resource_folder = "_resources"):
    #Формируем словарь
    props = {}
    props['folder_to_save'] = folder_to_save
    props['date'] = date
    props['time'] = time
    props['tags'] = tags
    props['note_name'] = note_name
    props['note_text'] = note_text
    props['attachments'] = attachments
    
    #Проверяем существование папки
    true_folder_to_save = os.path.isdir(folder_to_save)
    if not true_folder_to_save: raise Exception("true_folder_to_save: false")
    
    ##Проверяем наличие файла с таким же названием заметки 
    #Ставим вместо пробелов знаки подчёркивания и ограничиваем число символов 45
    note_name_no_spaces_tr = note_name[:45].replace(' ', '_')
    
    #Проверяем есть ли такое уже в папке
    true_note_name_created = os.path.isfile(folder_to_save + os.path.sep + note_name_no_spaces_tr + '.md')
    #Если есть - добавляем к названию заметки дату и время
    if true_note_name_created: note_name_no_spaces_tr += "_" + str(datetime.datetime.now()).replace(" ", "").replace("-", ""). replace(":","")
    
    print(folder_to_save + os.path.sep + note_name_no_spaces_tr + '.md')
    
    attachments_saved = []
    #Смотрим есть ли вложения
    if len(attachments) > 0:
        #Проверяем существование папки вложений
        true_resource_folder = os.path.isdir(folder_to_save + os.path.sep + resource_folder)
        if not true_resource_folder: raise Exception("true_resource_folder: false")

        #Копируем вложения в вложенную папку _resources
        for attach in attachments:
            attach_file_new_name = os.path.basename(attach).replace(" ", "")
            shutil.copyfile(attach, folder_to_save + os.path.sep + resource_folder + os.path.sep + attach_file_new_name)
            attachments_saved.append(attach_file_new_name)
    
    #Формируем содержимое файла
    with open(folder_to_save + os.path.sep + note_name_no_spaces_tr + '.md', 'w', encoding="utf-8") as f:
        f.write("---\n")
        f.write(f'tags: ["#{date[-4:]} #из_telegram"]\n')
        f.write(f'created_at: "{date} {time}"\n')
        f.write("---\n")
        f.write("\n\n")
        f.write(f"# {note_name}\n")
        f.write(note_text+"\n\n")
        
        #Дописываем список вложений с ссылкой на файл в вложенной папке _resources
        for attach in attachments_saved:
            f.write(f"![[{attach}]]" + "\n\n")
        
        f.write(f"created_at: {date} {time}\n")
        f.close()
    
    return 0


def checkEmail():
    # SSL Context docs https://docs.python.org/3/library/ssl.html#ssl.create_default_context
    # Docs: https://pypi.org/project/imbox/ , https://github.com/martinrusev/imbox

    with Imbox(CFG_IMAP_HOST,

            username=CFG_IMAP_LOGIN,
            password=CFG_IMAP_PASS,
            ssl=True,
            ssl_context=None,
            starttls=False) as imbox:

        # Unread messages
        unread_inbox_messages = imbox.messages(unread=True)
        

        for uid, message in unread_inbox_messages:
            # Every message is an object with the following keys
            note_subject = message.subject
            date = parse(message.date).strftime("%d.%m.%Y")
            year = parse(message.date).strftime("%Y")
            time = parse(message.date).strftime("%H:%M")
            text = message.body['plain'][0]
            imbox.mark_seen(uid)

            writer(f"{CFG_FOLDER_TO_WRITE}", 
            date,
            time, 
            [f"{year}"], 
            note_subject, 
            text, 
            [],
            f"{CFG_FOLDER_RESOURCES}"
            )

schedule.every(1).minutes.do(checkEmail)

while True:
    schedule.run_pending()
    time.sleep(1)