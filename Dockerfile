FROM python:3.9

RUN curl 													\
		-L https://yt-dl.org/downloads/latest/youtube-dl    \
		-o /usr/local/bin/youtube-dl 				     && \
    chmod a+rx /usr/local/bin/youtube-dl 				 && \
    mkdir -p /data/share 								 && \
    chmod -R 777 /data/share							 && \
    python3 -m pip install feedparser==6.0.2

COPY check_feed.py ./

ENTRYPOINT ["python3", "check_feed.py"]

# Run command:
# docker run -it --rm --name yt-cache --mount type=bind,source=/data/share,target=/data/share 3digitdev/dev/yt-cache:latest