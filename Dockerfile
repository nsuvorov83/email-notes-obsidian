FROM python:3.9.12

ADD ./src/email-notes-obsidian.py /
RUN pip install python-dateutil
RUN pip install imbox
RUN pip install schedule
CMD python email-notes-obsidian.py

ENV PUID=1000 PGID=1000