#
# created by Tarun and Pitchappan on 20/10/18
#
# Project Accio
#
import traceback
import gmplot
import socket
import os
import time
import random

from mesh.node import Node
from mesh.links import UDPLink, VirtualLink
from mesh.programs import Printer, Switch, BaseProgram
from mesh.filters import UniqueFilter


def hops(node1, node2):
    if node1 == node2:
        return 0
    elif set(node1.interfaces) & set(node2.interfaces):
        return 1
    else:
        return 0

def linkmembers(nodes, link):
    return [n for n in nodes if link in n.interfaces]

def eigenvalue(nodes, node=None):
    #calculate the eigenvalue (number of connections) for a given node
    if node is None:
        return sorted([eigenvalue(nodes, n) for n in nodes])[0]  # return lowest eigenvalue
    else:
        return len([1 for n in nodes if hops(node, n)])

def ask(type, question, fallback=None):
    value = input(question)
    if type == bool:
        if fallback:
            return not value[:1].lower() == "n"
        else:
            return value[:1].lower() == "y"
    try:
        return type(value)
    except Exception:
        return fallback


HELP_STR = """Type a nodelabel or linkname to send messages.
        e.g. [$]:DeathEater
             [DeathEater]<en1> Wayne:hi
        or
             [$]:JEnglish01
             <JEnglish01>(3) [n1,n4,n3]:let's help other survivors"""


if __name__ == "__main__":
    port = 2001

    num_nodes = ask(int, "number of nodes ?     [50000]:",      50000)
    num_links = ask(int, "number of links ?      [50]:",       50)
    real_link = ask(bool, "Link to local networks?        [y]/n:",    True)

    print('Reaching Out')
    links = []
    if real_link:
        links += [UDPLink('en0', port), UDPLink('en1', port+1), UDPLink('en2', port+2)]
    links += [
        VirtualLink("vl%s" % (x+1))
        for x in range(num_links)
    ]

    print('Establishing connection')
    nodes = [
        Node(None, "n%s" % x, Filters=[UniqueFilter], Program=random.choice((Printer, Switch)))
        for x in range(num_nodes)
    ]

    print("You are now a part of something bigger")
    [link.start() for link in links]
    for node in nodes:
        node.start()
        print("%s:%s" % (node, node.interfaces))

    print(HELP_STR)
    dont_exit = True
    try:
        while dont_exit:
            command = str(input("[$]:"))
            if command[:1] == "l":
                link = [l for l in links if l.name[1:] == command[1:]]
                if link:
                    link = link[0]
                    link_members = linkmembers(nodes, link)
                    message = str(input("%s(%s) %s:" % (link, len(link_members), link_members)))
                    if message == "stop":
                        link.stop()
                    else:
                        link.send(bytes(message, 'UTF-8'))  # convert python str to bytes for sending over the wire
                else:
                    print("Not a link.")

            elif command[:1] == "n":
                node = [n for n in nodes if n.name[1:] == command[1:]]
                if node:
                    node = node[0]
                    message = str(input("%s<%s> ∂%s:" % (node, node.interfaces, eigenvalue(nodes, node))))
                    if message == "stop":
                        node.stop()
                    else:
                        node.send(bytes(message, 'UTF-8'))  # convert python str to bytes for sending over the wire
                else:
                    print("Not a node.")

            elif command[:1] == "h":
                print(HELP_STR)
            else:
                print("Invalid command.")
                print(HELP_STR)

            time.sleep(0.5)
    except BaseException as e:
        intentional = type(e) in (KeyboardInterrupt, EOFError)
        if not intentional:
            traceback.print_exc()
        try:
            assert all([n.stop() for n in nodes]), 'Some nodes failed to stop.'
            assert all([l.stop() for l in links]), 'Some links failed to stop.'
        except Exception as e:
            traceback.print_exc()
            intentional = False
        print("EXITING CLEANLY" if intentional else "EXITING BADLY")
        raise SystemExit(int(not intentional))

class ChatProgram(BaseProgram):
    def recv(self, packet, interface):
        scale=input("scale:")
        string1=packet.decode()
        locm=string1.split(',')
        gmap1 = gmplot.GoogleMapPlotter(locm[0],locm[1], scale)
        gmap1.draw("C:\SurvivorLocation\map11.html")



if __name__ == "__main__":
    links = [UDPLink('en0', 2010), UDPLink('en1', 2011), UDPLink('en2', 2012), UDPLink('en3', 2013)]
    node = Node(links, 'me', Filters=(UniqueFilter,), Program=ChatProgram)
    [link.start() for link in links]
    node.start()


    try:
        while True:
            print("------------------------------")
            message = input('<< ')
            node.send(bytes(message, 'UTF-8'))
            time.sleep(0.3)

    except (EOFError, KeyboardInterrupt):   # graceful CTRL-D & CTRL-C
        node.stop()
        [link.stop() for link in links]
