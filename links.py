#
# created by Tarun and Pitchappan on 20/10/18
#
# Project Accio
#
import threading
from queue import Queue, Empty


from time import sleep
from random import randint
from collections import defaultdict

import select
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST

try:
    from socket import SO_REUSEPORT
    IS_BSD = True
except:
    IS_BSD = False


class VirtualLink:
    broadcast_addr = "00:00:00:00:00:00:00"

    def __init__(self, name="admin"):
        self.name = name
        self.keep_listening = True

        self.inq = defaultdict(Queue)
        self.inq[self.broadcast_addr] = Queue()

    def __repr__(self):
        return "<%s>" % self.name

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.inq)

    def log(self, *args):
        print("%s %s" % (str(self).ljust(8), " ".join([str(x) for x in args])))

    def start(self):
        self.log("ready.")
        return True

    def stop(self):
        self.keep_listening = False
        if hasattr(self, 'join'):
            self.join()
        self.log("Went down.")
        return True

    def recv(self, mac_addr=broadcast_addr, timeout=0):
        if self.keep_listening:
            try:
                return self.inq[str(mac_addr)].get(timeout=timeout)
            except Empty:
                return ""
        else:
            self.log("is down.")

    def send(self, packet, mac_addr=broadcast_addr):
        if self.keep_listening:
            if mac_addr == self.broadcast_addr:
                for addr, recv_queue in self.inq.items():
                    recv_queue.put(packet)
            else:
                self.inq[mac_addr].put(packet)
                self.inq[self.broadcast_addr].put(packet)
        else:
            self.log("is down.")

class UDPLink(threading.Thread, VirtualLink):

    def __init__(self, name="en0", port=2001):
        threading.Thread.__init__(self)
        VirtualLink.__init__(self, name=name)
        self.port = port
        # self.log("starting...")
        self._initsocket()

    def __repr__(self):
        return "<" + self.name + ">"

    def _initsocket(self):
        self.send_socket = socket(AF_INET, SOCK_DGRAM)
        self.send_socket.setblocking(0)
        self.send_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.recv_socket = socket(AF_INET, SOCK_DGRAM)
        self.recv_socket.setblocking(0)
        if IS_BSD:
            self.recv_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        self.recv_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.recv_socket.bind(('', self.port))

    def run(self):
        read_ready = None

        while self.keep_listening:
            try:
                read_ready, w, x = select.select([self.recv_socket], [], [], 0.01)
            except Exception:
                pass

            if read_ready:
                packet, addr = read_ready[0].recvfrom(4096)
                if addr[1] == self.port:
                    for mac_addr, recv_queue in self.inq.items():
                        recv_queue.put(packet)
                else:
                    pass

    def send(self, packet, retry=True):
        addr = ('255.255.255.255', self.port)
        try:
            self.send_socket.sendto(packet, addr)
        except Exception as e:
            self.log("Link failed to send packet over socket %s" % e)
            sleep(0.2)
            if retry:
                self.send(packet, retry=False)

class IRCLink(threading.Thread, VirtualLink):
    def __init__(self, name='irc1', server='irc.freenode.net', port=6667, channel='##medusa', nick='bobbyTables'):
        threading.Thread.__init__(self)
        VirtualLink.__init__(self, name=name)
        self.name = name
        self.server = server
        self.port = port
        self.channel = channel
        self.nick = nick if nick != 'bobbyTables' else 'bobbyTables' + str(randint(1, 1000))
        self.log("starting...")
        self._connect()
        self._join_channel()
        self.log("irc channel connected.")

    def __repr__(self):
        return "<"+self.name+">"

    def stop(self):
        self.net_socket.send(b"QUIT\r\n")
        VirtualLink.stop(self)

    def _parse_msg(self, msg):
        if b"PRIVMSG" in msg:
            from_nick = msg.split(b"PRIVMSG ",1)[0].split(b"!")[0][1:]
            to_nick = msg.split(b"PRIVMSG ",1)[1].split(b" :",1)[0]
            text = msg.split(b"PRIVMSG ",1)[1].split(b" :",1)[1].strip()
            return (text, from_nick)
        elif msg.find(b"PING :",0,6) != -1:
            from_srv = msg.split(b"PING :")[1].strip()
            return ("PING", from_srv)
        return ("","")

    def _connect(self):
        self.log("connecting to server %s:%s..." % (self.server, self.port))
        self.net_socket = socket(AF_INET, SOCK_STREAM)
        self.net_socket.connect((self.server, self.port))
        self.net_socket.setblocking(1)
        self.net_socket.settimeout(2)
        msg = self.net_socket.recv(4096)
        while msg:
            try:
                msg = self.net_socket.recv(4096).strip()
            except Exception:
                msg = None

    def _join_channel(self):
        self.log("joining channel %s as %s..." % (self.channel, self.nick))
        nick = self.nick
        self.net_socket.settimeout(10)
        self.net_socket.send(('NICK %s\r\n' % nick).encode('utf-8'))
        self.net_socket.send(('USER %s %s %s :%s\r\n' % (nick, nick, nick, nick)).encode('utf-8'))
        self.net_socket.send(('JOIN %s\r\n' % self.channel).encode('utf-8'))
        msg = self.net_socket.recv(4096)
        while msg:
            if b"Nickname is already in use" in msg:
                self.nick += str(randint(1, 1000))
                self._join_channel()
                return
            elif b"JOIN" in msg:
                break
            try:
                msg = self.net_socket.recv(4096).strip()
            except:
                msg = None

    def run(self):
        self.log("ready to receive.")
        self.net_socket.settimeout(0.05)
        while self.keep_listening:
            try:
                packet = self.net_socket.recv(4096)
            except:
                packet = None
            if packet:
                packet, source = self._parse_msg(packet)
                if packet == "PING":
                    self.net_socket.send(b'PONG ' + source + b'\r')
                elif packet:
                    for mac_addr, recv_queue in self.inq.items():
                        # put the packet in that mac_addr recv queue
                        recv_queue.put(packet)
        self.log('is down.')

    def send(self, packet, retry=True):
        if not self.keep_listening:
            self.log('is down.')
            return

        try:
            for mac_addr, recv_queue in self.inq.items():
                recv_queue.put(packet)
            self.net_socket.send(('PRIVMSG %s :%s\r\n' % (self.channel, packet.decode())).encode('utf-8'))
        except Exception as e:
            self.log("Link failed to send packet over socket %s" % e)
            sleep(0.2)
            if retry:
                self.send(packet, retry=False)

class RawSocketLink(threading.Thread, VirtualLink):
    def __init__(self):
        raise NotImplementedError()


class MultiPeerConnectivityLink(threading.Thread, VirtualLink):

    def __init__(self):
        raise NotImplementedError()
