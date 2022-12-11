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
CFG_FOLDER_RESOURCES = os.environ.get('CFG_FOLDER_RESOURCES') #'%YOUR_CFG_FOLDER_RESOURCES%'

def writer(folder_to_save, date, time, tags = [], note_name = "", note_text = "", attachments_saved = [], resource_folder = "_resources"):
    
    #Checking folder for notes exists
    true_folder_to_save = os.path.isdir(folder_to_save)
    if not true_folder_to_save: raise Exception("true_folder_to_save: false")
    
    #45 symbols max, no spaces
    note_name_no_spaces_tr = note_name[:45].replace(' ', '_')
    
    #Checking same named file
    true_note_name_created = os.path.isfile(folder_to_save + os.path.sep + note_name_no_spaces_tr + '.md')
    #If true - add time to filename
    if true_note_name_created: note_name_no_spaces_tr += "_" + str(datetime.datetime.now()).replace(" ", "").replace("-", ""). replace(":","")
    
    #File content forming
    with open(folder_to_save + os.path.sep + note_name_no_spaces_tr + '.md', 'w', encoding="utf-8") as f:
        f.write("---\n")
        f.write(f'tags: ["#{date[-4:]} #из_telegram"]\n')
        f.write(f'created_at: "{date} {time}"\n')
        f.write("---\n")
        f.write("\n\n")
        f.write(note_text+"\n\n")
        
        #Writting attachments
        for attach in attachments_saved:
            f.write(f"![[{attach}]]" + "\n\n")
        
        #Writting footer
        f.write(f"## Other notes about this\n")
        f.write(f"```dataview\n")
        f.write(f'TABLE file.ctime as "Date"\n')
        f.write(f"FROM #tag\n")
        f.write(f"LIMIT 10\n")
        f.write(f"SORT file.ctime DESC\n")
        f.write(f"```\n")

        f.write(f"\n\ncreated_at: {date} {time}\n")
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
            text = ""
            
            if(len(message.body['plain'])>0):
                text = message.body['plain'][0]
            elif (len(message.body['html'])>0):
                text = message.body['html'][0]

            attachments_saved = []

            #Mark seen the message
            imbox.mark_seen(uid)

            #Parse attachments
            try:
                for idx, attachment in enumerate(message.attachments):
                    #Checking whether resource folder exists
                    print(f"{CFG_FOLDER_TO_WRITE}{os.path.sep}{CFG_FOLDER_RESOURCES}")
                    true_resource_folder = os.path.isdir(f"{CFG_FOLDER_TO_WRITE}{os.path.sep}{CFG_FOLDER_RESOURCES}")
                    if not true_resource_folder: raise Exception("true_resource_folder: false")#
                    
                    #Saving attachment straight into resource folder
                    att_fn = attachment.get('filename')
                    download_path = f"{CFG_FOLDER_TO_WRITE}{os.path.sep}{CFG_FOLDER_RESOURCES}{os.path.sep}{att_fn}"
                    with open(download_path, "wb") as fp:
                        fp.write(attachment.get('content').read())

                    #Appending just saved attachment into list of attachments to add to the note    
                    attachments_saved.append(att_fn)
            except Exception as e: 
                print(e)

            #Calling writer to write the note
            writer(
                f"{CFG_FOLDER_TO_WRITE}", 
                date,
                time, 
                [f"{year}"], 
                note_subject, 
                text, 
                attachments_saved,
                f"{CFG_FOLDER_RESOURCES}"
            )

#Make schedule
schedule.every(1).minutes.do(checkEmail)
while True:
    schedule.run_pending()
    time.sleep(1)