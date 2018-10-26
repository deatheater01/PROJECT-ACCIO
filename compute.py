#!/usr/bin/env pypy
import os
import time
import tqdm
import multiprocessing as mp
from bitstring import ConstBitStream
from PIL import Image



#horizontal= 80
#horizontal= 280
#horizontal= 217

#STAMP = "3162099"
#STAMP = "749113"
STAMP = "1297209"

def handleDump(fileObj):
    tech = []
    raw = ConstBitStream(fileObj)
    try:
        while True:
            tech.append(raw.read('floatle:32'))
    except:
        pass
    del(raw)
    return tech 


def processing(params):
    pStamp = params[0]
    pI = params[1]
    pJ = params[2]
    VER = params[3]
    HOR = params[4]
    PXLS = params[5]
    
    filen = open( 'SAMPLE_{0}_{1}_{2}.dmp'.format(pStamp, str(pI), str(pJ) ), 'rb')
    

    tech = handleDump(filen)
        
    filen.close()
    del(filen)

    average = sum(tech)/float(len(tech))
    
    colour = int( (average/100)*255 )
    hold = [ pStamp, pI, pJ, VER, HOR, colour ]
    del(tech)
    return hold



if __name__ == '__main__':
    
    VERTICAL = 80
    HORIZONTAL = 270
    
    IMG = Image.new('RGB', (HORIZONTAL, VERTICAL), 'black')
    PIXELS = IMG.load()

    # create file processing queue
    DUMPS = []
    for i in xrange(HORIZONTAL):
        for j in xrange(VERTICAL):
            DUMPS.append([ STAMP, i, j, VERTICAL, HORIZONTAL, 0])

    #  process the data
    pewl = mp.Pool(3)
    print("processing...")

    for PXL in tqdm.tqdm(pewl.imap_unordered(processing, DUMPS), total=len(DUMPS)):

        if PXL[1]/2 == PXL[1]/2.0:
            reverse = 0
        else:
            reverse = VERTICAL - 1

        PIXELS[ HORIZONTAL-1-PXL[1], abs(PXL[2] - reverse) ] = (PXL[5], PXL[5], PXL[5])
        
    print("completed...")
        
    IMG.show()
