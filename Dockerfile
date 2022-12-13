FROM dustynv/jetson-inference:r32.7.1
RUN pip install numpy && \
    pip install Flask && \
    pip install jsonpickle

RUN mkdir data
ADD data data

RUN mkdir detection &&\
    mkdir detection/img
COPY jetson_detection.py detection
COPY run.sh detection
# COPY setup.py detection

WORKDIR detection
# RUN python3 setup.py

EXPOSE 8080
CMD ["sh","./run.sh"]