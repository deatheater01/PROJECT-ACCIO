#
# created by Tarun and Pitchappan on 20/10/18
#
# Project Accio
#
import random
import threading
import time
from collections import defaultdict


from queue import Queue


from .filters import LoopbackFilter

class Node(threading.Thread):
    def __init__(self, interfaces=None, name="admin", promiscuous=False, mac_addr=None, Filters=(), Program=None):
        threading.Thread.__init__(self)
        self.name = name
        self.interfaces = interfaces or []
        self.keep_listening = True
        self.promiscuous = promiscuous
        self.mac_addr = mac_addr or self._generate_MAC(6, 2)
        self.inq = defaultdict(Queue)
        self.filters = [LoopbackFilter()] + [F() for F in Filters]
        self.program = Program(node=self) if Program else None

    def __repr__(self):
        return "[{0}]".format(self.name)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def _generate_MAC(segments=6, segment_length=2, delimiter=":", charset="0123456789abcdef"):
        addr = []
        for _ in range(segments):
            sub = ''.join(random.choice(charset) for _ in range(segment_length))
            addr.append(sub)
        return delimiter.join(addr)

    def log(self, *args):
        print("%s %s" % (str(self).ljust(8), " ".join(str(x) for x in args)))

    def stop(self):
        self.keep_listening = False
        if self.program:
            self.program.stop()
        self.join()
        return True

    def run(self):
        if self.program:
            self.program.start()
        while self.keep_listening:
            for interface in self.interfaces:
                packet = interface.recv(self.mac_addr if not self.promiscuous else "00:00:00:00:00:00")
                if packet:
                    self.recv(packet, interface)
                time.sleep(0.01)
        self.log("Stopped listening.")

    def recv(self, packet, interface):
        for f in self.filters:
            if not packet:
                break
            packet = f.tr(packet, interface)
        if packet:
            self.inq[interface].put(packet)

    def send(self, packet, interfaces=None):
        interfaces = interfaces or self.interfaces
        interfaces = interfaces if hasattr(interfaces, '__iter__') else [interfaces]

        for interface in interfaces:
            for f in self.filters:
                packet = f.tx(packet, interface)
            if packet:
                interface.send(packet)
