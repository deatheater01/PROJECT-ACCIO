#
# created by Tarun and Pitchappan on 20/10/18
#
# Project Accio
import os
import sys
import time
import serial
import socket
import random
import threading





milli_timestamp = lambda: int(round(time.time() * 1000))
def getData(conn, sync, timing):
    writing=False
    tid=0
    datafile=0
    while True:
        try:
            if sync["sync"] == True and writing == False:
                datafile = open('{0}.dmp'.format(sync["name"]), 'wb')
                sync["sync"] = False
                writing = True
                tid = milli_timestamp()
                
            ts = milli_timestamp()

            data = conn.recv(1024)
            if not data and datafile != 0:
                datafile.close()
                datafile = 0
                break
            
            if (ts - tid) < timing and writing == True and datafile != 0:
                datafile.write(data)
                
            elif datafile != 0:
                if not datafile.closed:
                    datafile.close()
                    datafile = 0
                    writing = False
        except Exception as e:
            print("Shit on fire,yo!")
            print(e)
            datafile.close()
            datafile = 0
            break
    return

    
def runThread(Sync):
    sock = socket.socket( socket.AF_INET, # Internet       
                          socket.SOCK_DGRAM) # UDP
    sock.bind(("0.0.0.0", 9000))
    
    threading.Thread(target=getData, args=[sock, Sync, 250]).start()
    print("[Listening on port 9000]")
    return

    
if __name__ == "__main__":


    

        

    
    s = serial.Serial('/dev/ttyACM0',115200)
    
    runThread(SAMPLE)
    

    s.write("$X\n")
    s.write("\r\n\r\n")
    s.write("$x\n")
    s.write("$X\n")
    print( 'starting in...')
    for sec in xrange(10):
        time.sleep(1)
        print (str(10 - sec) + '...')
    print( 'GO!')
    s.flushInput()
    s.write("$X\n")
    
    # Stream g-code to grbl
    for line in cmdStream:
        if line[0] == "#":
            print( line[1:])
            continue
        elif line[0] == "!":       #  write samples to a file
            SAMPLE["name"]=line[1:]
            SAMPLE["sync"]=True
            continue
        
        l = line.strip()
        print('Sending: ' + l + '\n')
        s.write(l + '\n')
        grbl_out = s.readline()
        print(' : ' + grbl_out.strip())
        
    # Wait here until grbl is finished to close serial port and file.
    raw_input("  Press <Enter> to exit and disable grbl.")
