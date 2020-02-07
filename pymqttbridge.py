#!/usr/bin/python
# coding=utf-8
"""Translate UDP messages from thread to mqtt messages for the internet."""
import socket
import paho.mqtt.client as mqtt
import serial
import logging
import argparse


def create_socket(ip, port):
    """Create Socket"""
    if ':' in ip:  # Create Ipv4/6 socket and bind to port
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip, port))
    return s


def parse_args():
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--serial',
                        dest='serial',
                        type=str,
                        help='Serial port, where a nrf52840 device can be found. Like /dev/ttyACM0. Default=%(default)',
                        default=None)
    parser.add_argument('-sp', '--speed',
                        dest='speed',
                        type=int,
                        help='Speed which should be used at the serial port. Default=%(default)',
                        default=115200)
    parser.add_argument('-t', '--timeout',
                        dest='timeout',
                        type=int,
                        help='Timeout for serial console in seconds. Useful to not get stuck. Default=%(default)',
                        default=2)
    parser.add_argument('-b', '--broker',
                        dest='broker',
                        type=str,
                        help='IP of the MQTTBroker where the messages should be send to. Default=%(default)',
                        default=None)
    parser.add_argument('-if', '--interface',
                        dest='interface',
                        type=str,
                        help='Ip of the interface which should be used to connect to broker. Default %(default)',
                        default="")
    parser.add_argument('-p', '--port',
                        dest='port',
                        type=int,
                        help='Port where to find the broker at. Default %(default)',
                        default=1883)
    parser.add_argument('-u', '--user',
                        dest='user',
                        type=str,
                        help='Set user for autentification at broker. Default %(default)',
                        default=None)
    parser.add_argument('-pw', '--password',
                        dest='password',
                        type=str,
                        help='Set password for autentification at broker. Default %(default)',
                        default=None)
    parser.add_argument('-c', '--channel',
                        dest='channel',
                        type=str,
                        help='Specify the mqtt channel messages should be send to. Default %(default)',
                        default='test')
    parser.add_argument('-l', '--loglevel',
                        dest='loglevel',
                        type=str,
                        help='Set loglevel to info or debug. Default %(default)',
                        default='info')
    return parser.parse_args()


def serial_connect(port=None, speed=None, timeout=None):
    """Connect to serial port and return it or die."""
    if not isinstance(port, str) or not isinstance(speed, int):
        return  # Die in case of luser
    timeout = timeout if timeout else 10
    try:
        serial_port = serial.Serial(port, speed, timeout=timeout)
    except ValueError:
        return  # Die an case of luser
    except serial.SerialException:
        logging.error('Cannot find or use device at port {}'.format(port))
        return
    if serial_port.isOpen():
        logging.debug('Port open at {}'.format(serial_port.name))
    return serial_port


def mqtt_connect(broker=None, port=1883, username=None, password=None, channel=None, interface=""):
    """Connect to serial port and return it or die"""
    if not isinstance(broker, str) or not isinstance(channel, str):
        return  # Die in case of luser
    mqttclient = mqtt.Client('P1')
    if username is not None:
        mqttclient.username_pw_set(username, password=password)
    mqttclient.connect(broker, port=port, keepalive=1, bind_address=interface)
    return mqttclient


def bridge(serialport=None, mqttclient=None, channel='test'):
    """Read incomming messages from serial port and bridge them to mqtt."""
    if serialport is None or mqttclient is None:
        return
    serialport.reset_input_buffer()
    serialport.write('\r\n'.encode('ascii'))
    serialport.write('udp open\r\n'.encode('ascii'))
    serialport.write('udp bind :: 1212\r\n'.encode('ascii'))
    serialport.reset_input_buffer()
    serialport.write('ipaddr\r\n'.encode('ascii'))
    while True:
        serialport.write('\r\n'.encode('ascii'))
        try:
            data = [line.decode('ascii')[:-2] for line in serialport.readlines()
                    if line not in [b'\r\n', b'> \r\n', b'> ']]
        except UnicodeDecodeError:
            logging.debug('UnicodeDecodeError')
            continue
        for line in data:
            if 'bytes from' in line:
                sline = line.split(' ')
                if sline[0] == '>':
                    sline = sline[1:]
                mqttclient.reconnect()
                mqttclient.publish(channel, sline[-1].replace(';', ' '))
            else:
                logging.debug(line)


if __name__ == '__main__':
    args = parse_args()
    llevel = logging.DEBUG if args.loglevel == 'debug' else logging.INFO
    logging.basicConfig(
        level=llevel, format='%(asctime)s %(levelname)s\t %(message)s', filemode='w')
    serial = serial_connect(port=args.serial, speed=args.speed, timeout=args.timeout)
    mqttcli = mqtt_connect(broker=args.broker, port=args.port, username=args.user, password=args.password,
                           channel=args.channel, interface=args.interface)
    if serial is None or mqttcli is None:
        quit(1)
    try:
        bridge(serialport=serial, mqttclient=mqttcli, channel=args.channel)
    except KeyboardInterrupt:
        pass
    finally:
        serial.close()
        mqttcli.disconnect()
