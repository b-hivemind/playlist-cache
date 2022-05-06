FROM python:3.9-alpine

COPY .cache playlist_cache.py lib.py deploy.py /playlist_cache/
COPY auth/ /playlist_cache/auth

COPY config.json /config/

WORKDIR /playlist_cache
COPY requirements.txt /playlist_cache
RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "deploy.py" ]
