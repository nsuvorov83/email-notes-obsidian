from imbox import Imbox
from dateutil.parser import parse
import datetime
import os
import schedule
import time
import yadisk
from io import BytesIO
import ssl


#Configuration
CFG_IMAP_LOGIN = os.environ.get('CFG_IMAP_LOGIN') #'%YOUR_IMAP_LOGIN%'
CFG_IMAP_PASS = os.environ.get('CFG_IMAP_PASS') #'%YOUR_IMAP_PASS%'
CFG_IMAP_HOST = os.environ.get('CFG_IMAP_HOST') #'%YOUR_IMAP_HOST%'
CFG_IMAP_CHECKING_INTERVAL = os.environ.get('CFG_IMAP_CHECKING_INTERVAL') #'%CFG_IMAP_CHECKING_INTERVAL%'
CFG_FOLDER_TO_WRITE = os.environ.get('CFG_FOLDER_TO_WRITE') #'%YOUR_FOLDER_TO_WRITE_NOTES%'
CFG_FOLDER_RESOURCES = os.environ.get('CFG_FOLDER_RESOURCES') #'%YOUR_CFG_FOLDER_RESOURCES%'
CFG_YDXDISK_CLIENT_ID = os.environ.get('CFG_YDXDISK_CLIENT_ID') #'%YOUR_CFG_YDXDISK_CLIENT_ID%'
CFG_YDXDISK_SECRET = os.environ.get('CFG_YDXDISK_SECRET') #'%YOUR_CFG_YDXDISK_SECRET%'
CFG_YDXDISK_TOKEN = os.environ.get('CFG_YDXDISK_TOKEN') #'%YOUR_CFG_YDXDISK_TOKEN%'

def writer(
    client,
    folder_to_save,  
    tags=[], 
    note_name="", 
    note_text="", 
    attachments_saved=[], 
    resource_folder="_resources"
):
    """
    Writes note to Obsidian on Yandex.Disk
    Getting auth token: https://oauth.yandex.ru/authorize?response_type=token&client_id=<application_id>
    
    Args:
        client: yadisk.Client - авторизованный клиент Яндекс.Диска
        folder_to_save: str - путь к папке на Яндекс.Диске
        tags: list - список тегов
        note_name: str - название заметки
        note_text: str - текст заметки
        attachments_saved: list - список вложений
        resource_folder: str - папка для ресурсов
    """
    
    #Декодируем полученный
    note_text_decoded = decode_unicode_escapes(note_text)
    
    # Проверяем валидность токена
    if not client.check_token():
        raise Exception("Invalid Yandex.Disk token")
    
    # Проверяем существование папки на Яндекс.Диске
    if not client.exists(folder_to_save):
        raise Exception(f"Folder does not exist on Yandex.Disk: {folder_to_save}")
    
    # 45 symbols max, no spaces
    note_name_no_spaces_tr = note_name[:45].replace(' ', '_')
    
    # Формируем полный путь к файлу на Яндекс.Диске
    remote_file_path = f"{folder_to_save}/{note_name_no_spaces_tr}.md"

    # Datetime for now
    now = datetime.datetime.now()
    
    # Проверяем существование файла с таким именем
    if client.exists(remote_file_path):
        timestamp = str(now).replace(" ", "").replace("-", "").replace(":", "")
        note_name_no_spaces_tr += "_" + timestamp
        remote_file_path = f"{folder_to_save}/{note_name_no_spaces_tr}.md"
    
    # Создаем папку для ресурсов, если её нет
    resource_dir = f"{folder_to_save}/{resource_folder}"
    if not client.exists(resource_dir):
        client.mkdir(resource_dir)
    
    file_attachments_names = []  # Список только имен файлов для вставки в заметку
    
    # Загружаем вложения на Яндекс.Диск
    for attach in attachments_saved:
        att_fn = attach['filename']
        file_like_object = attach['content']
        
        # Перемещаем курсор в начало файла
        file_like_object.seek(0)
        
        # Загружаем вложение на Яндекс.Диск
        remote_attach_path = f"{folder_to_save}/{resource_folder}/{att_fn}"

        try:
            client.upload(file_like_object, remote_attach_path)
        except Exception as e: 
                print(e)

        
        # Добавляем имя файла для вставки в заметку
        file_attachments_names.append(att_fn)
    
    # Формируем содержимое файла ПОСЛЕ загрузки вложений
    file_content = "---\n"
    file_content += f'tags:\n'
    file_content += f'  - {now.year}y\n'
    file_content += f'  - из_telegram\n'
    file_content += f'created_at: "{now.year}-{now.month}-{now.day}T{now.hour}:{now.minute}:{now.second}"\n'
    file_content += "---\n"
    file_content += "\n\n"
    file_content += note_text_decoded + "\n\n"
    
    # Добавляем вложения (теперь используем file_attachments_names)
    for attach_name in file_attachments_names:
        file_content += f"![[{attach_name}]]" + "\n\n"
    
    # Добавляем футер
    file_content += f"## Other notes about this\n"
    file_content += f"```dataview\n"
    file_content += f'TABLE file.ctime as "Date"\n'
    file_content += f"FROM #tag\n"
    file_content += f"LIMIT 10\n"
    file_content += f"SORT file.ctime DESC\n"
    file_content += f"```\n"
    file_content += f"\n\ncreated_at: {now.day}.{now.month}.{now.year} {now.hour}:{now.minute}:{now.second}\n"
    
    # Загружаем заметку на Яндекс.Диск
    file_bytes = file_content.encode('utf-8')
    file_like_object = BytesIO(file_bytes)
    client.upload(file_like_object, remote_file_path)
    
    return 0


def checkEmail():
    """
    Checks a special mailbox (letters marked unread only) and prepare note to write by writer
    """
    # SSL Context docs https://docs.python.org/3/library/ssl.html#ssl.create_default_context
    # Docs: https://pypi.org/project/imbox/ , https://github.com/martinrusev/imbox

    # Создаем SSL контекст без проверки сертификата
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    with Imbox(CFG_IMAP_HOST,
            username=CFG_IMAP_LOGIN,
            password=CFG_IMAP_PASS,
            ssl=True,
            ssl_context=ssl_context,
            starttls=False) as imbox:

        # Unread messages
        unread_inbox_messages = imbox.messages(unread=True)
        

        for uid, message in unread_inbox_messages:
            # Every message is an object with the following keys
            note_subject = message.subject
            text = ""
            
            if(len(message.body['plain'])>0):
                text = message.body['plain'][0]
            elif (len(message.body['html'])>0):
                text = message.body['html'][0]
            attachments_saved = []

            #Mark seen the message
            imbox.mark_seen(uid)

            #Parse attachments
            now = datetime.datetime.now()
            try:
                for idx, attachment in enumerate(message.attachments):
                    att_fn = attachment.get('filename')
                    
                    # Создаем BytesIO объект в памяти (НЕ загружаем на Яндекс.Диск!)
                    attachment_content = attachment.get('content').read()
                    file_like_object = BytesIO(attachment_content)
                    
                    # Сохраняем и объект BytesIO и имя файла
                    attachments_saved.append({
                        'filename': str(now).replace(":", "")+att_fn,
                        'content': file_like_object  # BytesIO объект в памяти
                    })
                    
            except Exception as e: 
                print(e)

            # Setting Yandex.Disk client 
            client = yadisk.Client(f"{CFG_YDXDISK_CLIENT_ID}", f"{CFG_YDXDISK_SECRET}", f"{CFG_YDXDISK_TOKEN}")

            #Calling writer to write the note
            writer(
                client,
                f"{CFG_FOLDER_TO_WRITE}", 
                [], 
                note_subject, 
                text, 
                attachments_saved,
                f"{CFG_FOLDER_RESOURCES}"
            )


def decode_unicode_escapes(text):
    """
    Decodes Unicode escape sequences into normal text

    Args:
        text: str - text to decode
    """
    if not text:
        return text
    
    # Если текст содержит двойные обратные слеши \\u, декодируем их
    if '\\\\u' in text or '\\u' in text:
        try:
            # Метод 2: через latin-1 encode + unicode_escape decode
            decoded = text.encode('latin-1').decode('unicode_escape')
            return decoded
        except Exception as e:
            print(f"Decoding failed: {e}")
            return text
    
    return text

#Make schedule
schedule.every(int(CFG_IMAP_CHECKING_INTERVAL)).minutes.do(checkEmail)
while True:
    schedule.run_pending()
    time.sleep(1)