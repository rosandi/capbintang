#!/usr/bin/env python3

import cv2 as cv
import logging as lg
import time
import re
import sys
import numpy as np
from tkinter import *
from tkinter import _setit
from PIL import Image,ImageTk

lg.basicConfig(level=lg.INFO,format='%(levelname)s: %(message)s')

ready=False
dnames=[]
current=""
outname='out'
nburst=10
navg=10
fid=0
bid=0
dfactor=5
mode=()
boxsize=(800,600)
cropping=False
setzone=False
cropbox=[]
cropvel=[0,0]
aspect=boxsize[0]/boxsize[1]
statstr='stream off'
stream_stop_confirmed=True

# default camera device

ndev=0
streamcap=cv.VideoCapture(0)
if not streamcap.isOpened():
    print("can not find video device...")

# close it again
streamcap.release()

### key binding ###
def enable_keys(e=None):
    #print('enabling shortcuts...')
    capwin.bind('<q>',winclose) # quit
    capwin.bind('<c>',docap)   # save
    capwin.bind('<w>',dosave)   # save
    capwin.bind('<b>',doburst)  # burst saving
    capwin.bind('<v>',dosum)    # image sum saving
    capwin.bind('<a>',doavg)    # image sum+average saving
    capwin.bind('<s>',togglestream) # toggle streaming
    capwin.bind('<r>',cropreset) # reset digital crop zoom
    capwin.bind('<m>',measuredrift) # measure image drift
    capwin.bind('<Right>',vhorinc)
    capwin.bind('<Left>',vhordec)
    capwin.bind('<Down>',vverinc)
    capwin.bind('<Up>',vverdec)

def disable_keys(e=None):
    #print('unbinding shotcuts...')
    capwin.unbind('<q>')
    capwin.unbind('<c>')
    capwin.unbind('<w>')
    capwin.unbind('<b>')
    capwin.unbind('<v>')
    capwin.unbind('<a>')
    capwin.unbind('<s>')
    capwin.unbind('<r>')
    capwin.unbind('<m>')
    capwin.unbind('<Right>')
    capwin.unbind('<Left>')
    capwin.unbind('<Down>')
    capwin.unbind('<Up>')
####

def vhorinc(e=None):
    global cropvel
    if cropping:
        cropvel[0]+=1

def vhordec(e=None):
    global cropvel
    if cropping:
        cropvel[0]-=1

def vverinc(e=None):
    global cropvel
    if cropping:
        cropvel[1]+=1

def vverdec(e=None):
    global cropvel
    if cropping:
        cropvel[1]-=1
    
def nburst_get(e=None):
    global nburst
    st=re.sub('[^0-9]','',enum.get().strip())
    nburst=int(st)
    enum.delete(0,END)
    enum.insert(0,"%d"%(nburst))
    enable_keys()

def navg_get(e=None):
    global navg
    st=re.sub('[^0-9]','',eavg.get().strip())
    navg=int(st)
    eavg.delete(0,END)
    eavg.insert(0,"%d"%(navg))
    enable_keys()

def fname_get(e=None):
    global outname,fid,bid
    tmpname=re.sub(' ','',fname.get())
    fname.delete(0,END)
    fname.insert(0,tmpname)
    if tmpname != outname:
        outname=tmpname
        fid=0
        bid=0
    enable_keys()

def dfact_get(e=None):
    global dfactor
    st=re.sub('[^0-9]','',dfact.get().strip())
    dfactor=int(st)
    dfact.delete(0,END)
    dfact.insert(0,"%d"%(dfactor))
    enable_keys()
    
##########################################
    
is_streaming=False
imgid=0
cr=0

def drawbox(img,save=False):
    global cropbox,tkimg,imgid,fid

    simg=img.resize(boxsize)
    
    if cropping:
        r=np.abs(cropbox[0]-cropbox[2])/np.abs(cropbox[1]-cropbox[3])
        
        if r<aspect:
            bs=(int(boxsize[1]*r),boxsize[1])
        else:
            bs=(boxsize[0],int(boxsize[0]/r))

        simg=simg.crop(cropbox).resize(bs,Image.ANTIALIAS)

        cr=cropbox.copy()
        
        cropbox[0]+=cropvel[0]
        cropbox[1]+=cropvel[1]
        cropbox[2]+=cropvel[0]
        cropbox[3]+=cropvel[1]
        
        if cropbox[0]<0 or cropbox[2]<0 or cropbox[1]>boxsize[0] or cropbox[3]>boxsize[1]:
            cropbox=cr.copy()
        MPos.config(text="%s cropzone:(%d,%d)(%d,%d) delta:(%d,%d)"%
                    (statstr,cropbox[0],cropbox[1],cropbox[2],cropbox[3],cropvel[0],cropvel[1]))
    else:
        MPos.config(text=statstr)

    if imgid:
        ibox.delete(imgid)

    tkimg=ImageTk.PhotoImage(simg)
    imgid=ibox.create_image(boxsize[0]/2,boxsize[1]/2,image=tkimg)
    ibox.update()
    
    if save:
        stnm='%s-%04d.jpg'%(outname,fid)
        if cropping:
            # save screen image if cropping is active
            simg.save(stnm,'JPEG')
        else:
            # otherwise wave the original image
            img.save(stnm,'JPEG')
        fid+=1
        print('file saved to: ',stnm)

def dostream():
    global ndev,streamcap,stream_stop_confirmed

    if streamcap.isOpened():
        status,frame=streamcap.read()    
        imdata=cv.cvtColor(frame,cv.COLOR_BGR2RGB)
        img=Image.fromarray(imdata,mode='RGB')
        drawbox(img)
        capwin.after(1,dostream)
        stream_stop_cofirmed=False        
    else:
        stream_stop_cofirmed=True

def togglestream(e=None):
    global streamcap,statstr

    if streamcap.isOpened():
        streamcap.release()
        statstr='stream off'
    else:
        streamcap=cv.VideoCapture(ndev)
        statstr='stream on'
        dostream()

def stopstream():
    global stream_stop_confirmed,streamcap,statstr
    
    if streamcap.isOpened():
        print("stopping video stream...")
        streamcap.release()
        statstr='stream off'
    
    while not stream_stop_confirmed:
        time.sleep(0.1)

#####################################
def docap(e=None,save=False):
    global ndev
    stopstream()
    
    cap=cv.VideoCapture(ndev)
    capwin.focus_force()
   
    status,frame=cap.read()
    if not status:
        print("error capturing image")
        return
    
    imdata=cv.cvtColor(frame,cv.COLOR_BGR2RGB)
    img=Image.fromarray(imdata,mode='RGB')
    drawbox(img,save)
    cap.release()

def dosave(e=None):
    docap(e,True)

############## BURST CAPTURE ################
def doburst(e=None):
    global bid,outname,ndev
    capwin.focus_force()
    stopstream()
    nburst_get()
    
    print("burst capturing... %d images"%(nburst))
    
    cap=cv.VideoCapture(ndev)
    
    tmpnm=outname
    outname="%s-%04d"%(tmpnm,bid) 
    
    ntaken=0
    while ntaken<nburst:
        for i in range(framepack):
            status,frame=cap.read()
            if not status:
                print("error capturing image")
                return
            if ntaken<nburst:
                imdata=cv.cvtColor(frame,cv.COLOR_BGR2RGB)
                img=Image.fromarray(imdata,mode='RGB')
                drawbox(img,True)
                print("done writing: %s-*.jpg"%(outname))
                bid+=1
            ntaken+=1
    outname=tmpnm
    cap.release()

############## SUM CAPTURE ##############
def dosum(e=None):
    global fid,ndev
    capwin.focus_force()
    stopstream()
    nburst_get()
    
    cap=cv.VideoCapture(ndev)
    
    print("sum capturing %d images"%(nburst))
    
    for ntaken in range(nburst):
        status,frame=cap.read()
        if not status:
            print("error capturing image")
            return 
        if ntaken==0: #first
            dat=np.array(frame,dtype='uint32')           
        else:
            dat=dat+frame

    # normalized to max value
    idat=255*dat.astype("float32")/float(np.amax(dat))
    imdata=cv.cvtColor(idat.astype("uint8"),cv.COLOR_BGR2RGB)
    img=Image.fromarray(imdata,mode='RGB')
    drawbox(img,True)
    
    if rawcheck.get():
        binfilename="%s-%04d"%(outname,fid)
        print("saving binary array (npy) to %s"%(binfilename))
        np.save(binfilename,dat)
    
    fid+=1
    cap.release()

########### AVERAGED CAPTURE ###########
def doavg(e=None):
    global fid,ndev
    capwin.focus_force()
    stopstream()
    
    nburst_get()
    cap=cv.VideoCapture(ndev)

    print("average capturing %d images"%(nburst))

    for ntaken in range(nburst):
        status,frame=cap.read()
        if not status:
            print("error capturing image")
            return
 
        if ntaken==0: #first
            dat=np.array(frame,dtype='uint32')          
        else:
            dat=dat+frame
    
    dat=dat/nburst

    imdata=cv.cvtColor(dat.astype('uint8'),cv.COLOR_BGR2RGB)
    img=Image.fromarray(imdata,mode='RGB')
    drawbox(img,True)
    
    if rawcheck.get():
        binfilename="%s-%04d"%(outname,fid)
        print("saving binary array (npy) to %s"%(binfilename))
        np.save(binfilename,dat)
    
    fid=fid+1
    cap.release()

####################################
def measuredrift(e):
    global outname,nburst
    print('measuring image drift')
    tmpnm=outname
    tmpnb=nburst
    tmpcrop=cropping
    cropping=False
    outname='drift'
    nburst=10
    doburst(e)
    outname=tmpnm
    nburst=tmpnb
    cropping=tmpcrop
    
def motionupdate(e):
    if setzone:
        MPos.config(text="x=%d y=%d"%(e.x,e.y))
        ibox.coords(cr,cropbox[0],cropbox[1],e.x,e.y)

def cropzone(e):
    global setzone,cropbox,cropping,cr

    stopstream()

    if cropping:
        cropreset()
        return
    
    setzone = not setzone
    
    if setzone:
        cropbox.append(e.x)
        cropbox.append(e.y)
        MPos.config(text="x=%d y=%d"%(e.x,e.y))
        ibox.bind('<Motion>',motionupdate)
        cr=ibox.create_rectangle(e.x,e.y,e.x,e.y,outline='blue')
    else:
        cropbox.append(e.x)
        cropbox.append(e.y)
        cropping=True
        MPos.config(text="cropzone:(%d,%d)(%d,%d)"%(cropbox[0],cropbox[1],cropbox[2],cropbox[3]))
        ibox.unbind('<Motion>')
        ibox.delete(cr)
        docap()
        
def cropreset(e=None):
    global cropping,cropvel
    cropping=False
    cropbox.clear()
    MPos.config(text="")
    cropvel=[0,0,0,0]
    docap()

def changedev(*args):
    global ndev,sdev
    newdev=sdev.get()
    cap=cv.VideoCapture(newdev)
    if cap.isOpened():
        ndev=newdev
        cap.release()
    else:
        print("device number %d does not exist"%(newdev))
        sdev.set(ndev)
    
def winclose(e=None):
    capwin.destroy()

####### MAIN ######

#cap=cv.VideoCapture(ndev)

#if not cap.isOpened():
#    print('can not open device %d'%(ndev))
#    sys.exit()

#just read this amount at once
framepack=cv.CAP_PROP_BUFFERSIZE

print("camera buffer size: %d"%(framepack))

capwin=Tk()
capwin.title("Cap Bintang")
ctr=Frame(capwin)
cmd=Frame(capwin)
ibox=Canvas(capwin,width=boxsize[0],height=boxsize[1],bg='grey')

ctr.grid(row=0,padx=5,pady=5,sticky=(W,E,N))
cmd.grid(row=1,padx=5,pady=5,sticky=(W,E,S))
ibox.grid(column=1,row=0,rowspan=2,padx=5,pady=5,sticky=(W,N))


#### CONFIGURATION ####

rawcheck=IntVar(capwin)

Label(ctr,text="SETUP").grid(row=0,columnspan=2,sticky=(N,W,E))
Label(ctr,text="Device: ").grid(row=1,sticky=W)
Label(ctr,text="#Burst: ").grid(row=2,sticky=W)
Label(ctr,text="#Average: ").grid(row=4,sticky=W)
Label(ctr,text="Delay factor: ").grid(row=5,sticky=W)
Label(ctr,text="File name:").grid(row=6,sticky=W)

sdev=IntVar(capwin)
sdev.trace("w",changedev)
sdlist={0,1,2}
devlist=OptionMenu(ctr,sdev,*sdlist)

enum=Entry(ctr)
enum.insert(0,"%s"%(nburst))

enum.bind('<FocusIn>', disable_keys)
enum.bind('<FocusOut>', nburst_get)

craw=Checkbutton(ctr,text="Save raw data on sum-burst",variable=rawcheck)

eavg=Entry(ctr)
eavg.insert(0,"%s"%(navg))
eavg.bind('<FocusIn>', disable_keys)
eavg.bind('<FocusOut>', navg_get)

dfact=Entry(ctr)
dfact.insert(0,"%s"%(dfactor))
dfact.bind('<FocusIn>', disable_keys)
dfact.bind('<FocusOut>', dfact_get)

fname=Entry(ctr)
fname.insert(0,outname)
fname.bind('<FocusIn>', disable_keys)
fname.bind('<FocusOut>', fname_get)

devlist.grid(column=1,row=1,sticky=(E,W))
enum.grid(column=1,row=2,sticky=(E,W))
craw.grid(column=1,row=3,sticky=(E,W))
eavg.grid(column=1,row=4,sticky=(E,W))
dfact.grid(column=1,row=5,sticky=(E,W))
fname.grid(column=1,row=6,sticky=(E,W))

### COMMANDS BUTTON ###
CapBut=Button(cmd,text="Capture (c)", command=docap)
WriteBut=Button(cmd,text="Write out (w)", command=dosave)
BurstBut=Button(cmd,text="Burst write (b)", command=doburst)
SumBut=Button(cmd,text="Sum image write (v)", command=dosum)
AvgBut=Button(cmd,text="Sum Average write (a)", command=doavg)
StreamBut=Button(cmd,text="Toggle stream mode (s)", command=togglestream)
QBut=Button(cmd,text="Quit",width=10,command=winclose,bg="blue")

CapBut.pack(fill=X,padx=20)
WriteBut.pack(fill=X,padx=20)
BurstBut.pack(fill=X,padx=20)
SumBut.pack(fill=X,padx=20)
AvgBut.pack(fill=X,padx=20)
StreamBut.pack(fill=X,padx=20)
QBut.pack(pady=20)

MPos=Label(capwin)
MPos.grid(column=1,row=2)

ibox.bind('<Button-1>',cropzone)

ctr.update()
capwin.geometry("%dx%d"%(boxsize[0]+ctr.winfo_width()+20,boxsize[1]+40))
capwin.resizable(0, 0)
enable_keys()

capwin.mainloop()

if streamcap.isOpened():
    streamcap.release()
