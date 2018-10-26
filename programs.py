#
# created by Tarun and Pitchappan on 20/10/18
#
# Project Accio
#
import re


import os
import threading
from time import sleep

from queue import Empty


from .routers import MessageRouter


class BaseProgram(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.keep_listening = True
        self.node = node

    def run(self):
        while self.keep_listening:
            for interface in self.node.interfaces:
                try:
                    self.recv(self.node.inq[interface].get(timeout=0), interface)
                except Empty:
                    sleep(0.01)

    def stop(self):
        self.keep_listening = False
        self.join()

    def recv(self, packet, interface):
        pass

class Printer(BaseProgram):
    def recv(self, packet, interface):
        sleep(0.2)
        self.node.log(("\nPRINTER  %s" % interface).ljust(39), packet.decode())

class Switch(BaseProgram):
    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        if packet and other_ifaces:
            self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet.decode())
            self.node.send(packet, interfaces=other_ifaces)

class Cache(BaseProgram):
    def __init__(self, node):
        self.received = []
        BaseProgram.__init__(self, node)

    def recv(self, packet, interface):
        self.received.append(packet)


def R(pattern):
    return re.compile(pattern)


class RoutedProgram(BaseProgram):
    router = MessageRouter()

    def __init__(self, node):
        super(RoutedProgram, self).__init__(node)
        self.router.node = node

    def recv(self, packet, interface):
        message = packet.decode()
        self.node.log('\n< [RECV]  %s' % message)
        self.router.recv(self, message, interface)

    def send(self, message, interface):
        if not (hasattr(message, '__iter__') and not hasattr(message, '__len__')):
            # if message is not a list or generator
            message = [message]

        for line in message:
            line = line if type(line) in (str, bytes) else '{0}'.format(line)
            if not line.strip():
                continue

            self.node.log('\n> [SENT]  %s' % line)
            packet = bytes(line, 'utf-8') if type(line) is str else line
            self.node.send(packet, interface)


class RedisProgram(BaseProgram):
    def __init__(self, node, recv_key=None, send_key=None, redis_conf=None):
        super(RedisProgram, self).__init__(node)
        import redis
        pid = os.getpid()
        self.recv_key = recv_key or 'node-{}-recv'.format(pid)
        self.send_key = send_key or 'node-{}-send'.format(pid)
        self.nodeq = redis.Redis(**(redis_conf or {
            'host': '127.0.0.1',
            'port': 6419,
            'db': 0,
        }))

    def run(self):
        print('[√] Redis program is buffering IO to db:{0} keys:{1} & {2}.'.format(
            0, self.recv_key, self.send_key))

        while self.keep_listening:
            for interface in self.node.interfaces:
                if self.get_recvs(interface):
                    continue
                if self.put_sends():
                    continue

                sleep(0.01)

    def recv(self, packet, interface):
        print('[IN]:  {}'.format(packet))
        self.nodeq.rpush(self.recv_key, packet)

    def send(self, packet, interface=None):
        print('[OUT]: {}'.format(packet))
        self.node.send(packet, interface)

    def get_recvs(self, interface):
        try:
            msg = self.node.inq[interface].get(timeout=0)
            self.recv(msg, interface)
            return True
        except Empty:
            return False

    def put_sends(self):
        out = self.nodeq.rpop(self.send_key)
        if out:
            self.send(out)
            return True
        return False
