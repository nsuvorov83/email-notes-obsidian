FROM python:3.12

ADD ./src/email-notes-obsidian.py /
RUN pip install python-dateutil
RUN pip install imbox
RUN pip install schedule
RUN pip install yadisk
RUN pip install requests
CMD python email-notes-obsidian.py

ENV PUID=1000 PGID=1000