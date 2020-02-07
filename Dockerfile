FROM python:3
ADD pymqttbridge.py /
LABEL maintainer "Andreas Ingo Grohmann <andreas_ingo.grohmann@tu-dresden.de>"
RUN pip install paho-mqtt pyserial
CMD [ "python", "./pymqttbridge.py", "-s", "/dev/ttyACM0", "-b", "192.168.123.1", "-c", "test" ]

# -s serial port
# -sp speed
# -t timeout
# -b ip of mqttbroker
# -p port at broker
# -if outgoing interface
# -u username at broker
# -pw password at broker
# -c channel at broker
# docker build -t pymqttbridge .
# docker run -d --device=/dev/ttyACM0 pymqttbridge
