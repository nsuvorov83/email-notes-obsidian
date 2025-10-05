# E-mail service for Obsidian
Write Obsidian notes just send it with e-mail as in Evernote.

## Clone
```
git clone https://github.com/nsuvorov83/email-notes-obsidian.git && cd email-notes-obsidian
```

## Configure
Edit .env_example file and remove "_example" from its name.

## Run in docker
```
docker-compose up -d
```
## TODO
- [X] Базовый функционал бота
- [X] Перевод сервиса API Яндекс.Диска через yadisk
- [ ] Агрегирование заметок
- [ ] Возможность настройки шаблона названия заметки и тегов по умолчанию
