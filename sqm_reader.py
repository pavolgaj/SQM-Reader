#!/usr/bin/python3
# version 0.1.3 01-11-2022
import sys
import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import filedialog
import time
import asyncio
import threading
import math
import serial
import serial.tools.list_ports

def mpsas2nelm(mpsas):
    if mpsas>18.3: nelm=7.93-5*math.log10(math.pow(10,4.316-(mpsas/5.))+1)    #Scotopic vision
    else: nelm=4.305-5*math.log10(math.pow(10,2.316-(mpsas/5.))+1)      #Photopic vision
    return nelm


def read1(block=True):
    '''read one data'''
    if block:  #block buttons for 1 reading
        Button1.configure(state=tk.DISABLED)
        Button2.configure(state=tk.DISABLED)
        Button3.configure(state=tk.DISABLED)
        Button2.update()
        Button3.update()
    t0=time.time()
    com.write(b'rx\r')
    time.sleep(5)  #wait for completing measurements
    ans=com.readline().decode().strip()    
    #ans="r,-09.42m,0000005915Hz,0000000000c,0000000.000s, 027.0C"   #for testing...
    data=ans.split(',')     #r,-09.42m,0000005915Hz,0000000000c,0000000.000s, 027.0C -> r,mpsas,freq,period,per,temp    
    #t=time.strftime('%Y_%m_%d %H:%M:%S',time.localtime(t0))
    t=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t0))      #for better import to excel
    mpsas=float(data[1][:-1])   #mpsas
    nelm=round(mpsas2nelm(mpsas),2) #nelm
    temp=float(data[-1][:-1])  #temperature in C

    mpsasVar.set(mpsas)
    nelmVar.set(nelm)
    tempVar.set(temp)
    timeVar.set(t)

    if saveVar.get():
        if uniVar.get():
            name=pathVar.get()+'sqm_'+time.strftime('%Y_%m_%d')+'.csv'
            #not create new file after midnight
            if time.localtime().tm_hour<12 and not midnightVar.get():
                if os.path.isfile(pathVar.get()+'sqm_'+time.strftime('%Y_%m_%d',time.localtime(time.time()-86400))+'.csv'):
                    name=pathVar.get()+'sqm_'+time.strftime('%Y_%m_%d',time.localtime(time.time()-86400))+'.csv'
            if os.path.isfile(name): f=open(name,'a')
            else:
                f=open(name,'w')
                f.write('Date/Time,MPSAS,NELM,SerialNo,Protocol,Model,Feature,Temp(C)\n')
            tt=time.strftime('%d.%m.%Y %H:%M:%S',time.localtime(t0))
            f.write('%s,%5.2f,%5.2f,00000001,00000004,00000003,00000028,%4.1f\n' %(tt,mpsas,nelm,temp))
            
            f.close()        
        else:
            name=pathVar.get()+'sqm_'+time.strftime('%Y_%m_%d')+'.dat'
            #not create new file after midnight
            if time.localtime().tm_hour<12 and not midnightVar.get():
                if os.path.isfile(pathVar.get()+'sqm_'+time.strftime('%Y_%m_%d',time.localtime(time.time()-86400))+'.dat'):
                    name=pathVar.get()+'sqm_'+time.strftime('%Y_%m_%d',time.localtime(time.time()-86400))+'.dat'
            if os.path.isfile(name): f=open(name,'a')
            else:
                f=open(name,'w')
                f.write('Date Time MPSAS NELM Temp(C)\n')
                f.write('%s %5.2f %5.2f %4.1f\n' %(t,mpsas,nelm,temp))
            f.close()
    if block:  #unblock buttons for 1 reading
        Button1.configure(state=tk.NORMAL)
        Button2.configure(state=tk.NORMAL)
        Button3.configure(state=tk.NORMAL)
    return t0

async def read_loop():
    '''loop for repeated reading'''
    t0=0
    dt=60*dtVar.get()  #interval in sec
    while loopTest:
        if time.time()-t0>dt: t0=read1(block=False)
        await asyncio.sleep(0.1)

def stop():
    '''stop repeated reading'''
    global loopTest
    loopTest=False

def reading():
    '''start repeated reading'''
    global loop,loopTest
    Button1.configure(state=tk.DISABLED)
    Button2.configure(state=tk.DISABLED)
    Button3.configure(state=tk.DISABLED)
    Button4.configure(state=tk.NORMAL)
    Entry2.configure(state='readonly')
    loopTest=True
    loop=asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(read_loop())
    Button1.configure(state=tk.NORMAL)
    Button2.configure(state=tk.NORMAL)
    Button3.configure(state=tk.NORMAL)
    Button4.configure(state=tk.DISABLED)
    Entry2.configure(state=tk.NORMAL)

def init():
    '''init serial COM port'''
    global com
    com=serial.Serial(portVar.get())
    time.sleep(1)
    com.baudrate=baudVar.get()
    Button2.configure(state=tk.NORMAL)
    Button3.configure(state=tk.NORMAL)

def select_path(event):
    path=os.getcwd().replace('\\','/')
    if len(pathVar.get())>0:
        if os.path.isdir(pathVar.get()): path=pathVar.get()
    path=filedialog.askdirectory(parent=root,title='SQM Reader - data folder',initialdir=path)
    if len(path)>0:
        path=path.replace('\\','/')
        cwd=os.getcwd().replace('\\','/')+'/'
        if cwd in path: path=path.replace(cwd,'')    #save relative path
        if path==cwd[:-1]: path='./'
        if len(path)>0:
            if not path[-1]=='/': path+='/'
        pathVar.set(path)

def close():
    global root
    stop()
    try: com.close()
    except NameError: pass  #not used
    f=open('sqm_config.txt','w')
    f.write(portVar.get()+'\n')
    f.write(str(baudVar.get())+'\n')
    f.write(pathVar.get()+'\n')
    f.write(str(saveVar.get())+'\n')
    f.write(str(dtVar.get())+'\n')
    f.write(str(midnightVar.get())+'\n')
    f.write(str(uniVar.get())+'\n')
    f.close()
    root.destroy()
    root=None

root=tk.Tk()
root.geometry('400x350')
root.resizable(0,0)
root.title('SQM Reader')
root.protocol('WM_DELETE_WINDOW',close)
try: root.iconbitmap('sqm.ico')   #win
except:
    try: #linux
        img=tk.Image('photo',file='sqm.png')
        root.tk.call('wm','iconphoto',root._w,img)
    except: pass

portVar=tk.StringVar(root)
baudVar=tk.IntVar(root)
dtVar=tk.DoubleVar(root)
pathVar=tk.StringVar(root)
saveVar=tk.BooleanVar(root)
uniVar=tk.BooleanVar(root)
midnightVar=tk.BooleanVar(root)
mpsasVar=tk.DoubleVar(root)
nelmVar=tk.DoubleVar(root)
tempVar=tk.DoubleVar(root)
timeVar=tk.StringVar(root)
pathVar.set('./')

Label1=tk.Label(root)
Label1.place(relx=0.04,rely=0.03,height=21,width=30)
Label1.configure(text='Port')
Label1.configure(anchor='w')

TCombobox1=ttk.Combobox(root)
TCombobox1.place(relx=0.13,rely=0.03,relheight=0.06,relwidth=0.3)
TCombobox1.configure(values=sorted([x.device for x in serial.tools.list_ports.comports()]))
TCombobox1.configure(textvariable=portVar)
TCombobox1.configure(width=137)
TCombobox1.configure(state='readonly')

Label2=tk.Label(root)
Label2.place(relx=0.48,rely=0.03,height=21,width=63)
Label2.configure(text='Baudrate')
Label2.configure(anchor='w')

TCombobox2=ttk.Combobox(root)
TCombobox2.place(relx=0.65,rely=0.03,relheight=0.06,relwidth=0.3)
TCombobox2.configure(values=[9600,14400,19200,38400,56000,57600,115200,128000,256000])
TCombobox2.configure(textvariable=baudVar)
TCombobox2.configure(width=147)
TCombobox2.configure(state='readonly')

Button1=tk.Button(root)
Button1.place(relx=0.33,rely=0.11,height=29,width=127)
Button1.configure(text='Init')
Button1.configure(width=127)
Button1.configure(command=init)

Checkbutton1=tk.Checkbutton(root)
Checkbutton1.place(relx=0.04,rely=0.21,relheight=0.06,relwidth=0.4)
Checkbutton1.configure(justify=tk.LEFT)
Checkbutton1.configure(variable=saveVar)
Checkbutton1.configure(text='Save to file')
Checkbutton1.configure(anchor='w')

Checkbutton3=tk.Checkbutton(root)
Checkbutton3.place(relx=0.3,rely=0.21,relheight=0.06,relwidth=0.4)
Checkbutton3.configure(justify=tk.LEFT)
Checkbutton3.configure(variable=uniVar)
Checkbutton3.configure(text='Unihedron CSV')
Checkbutton3.configure(anchor='w')

Checkbutton2=tk.Checkbutton(root)
Checkbutton2.place(relx=0.6,rely=0.21,relheight=0.06,relwidth=0.5)
Checkbutton2.configure(justify=tk.LEFT)
Checkbutton2.configure(variable=midnightVar)
Checkbutton2.configure(text='New file after midnight')
Checkbutton2.configure(anchor='w')

Label3=tk.Label(root)
Label3.place(relx=0.04,rely=0.29,height=21,width=40)
Label3.configure(text='Path')
Label3.configure(anchor='w')

Entry1=tk.Entry(root)
Entry1.place(relx=0.15,rely=0.29,height=23,relwidth=0.81)
Entry1.configure(background='white')
Entry1.configure(width=436)
Entry1.configure(textvariable=pathVar)
Entry1.configure(state='readonly')
Entry1.bind('<Button-1>',select_path)

Button2=tk.Button(root)
Button2.place(relx=0.04,rely=0.4,height=29,width=59)
Button2.configure(text='Read')
Button2.configure(command=read1)
Button2.configure(state=tk.DISABLED)

Button3=tk.Button(root)
Button3.place(relx=0.22,rely=0.4,height=29,width=100)
Button3.configure(text='Read every')
Button3.configure(command=lambda: threading.Thread(target=reading).start())
Button3.configure(state=tk.DISABLED)

Entry2=tk.Entry(root)
Entry2.place(relx=0.5,rely=0.41,height=23,relwidth=0.15)
Entry2.configure(width=76)
Entry2.configure(textvariable=dtVar)

Label4=tk.Label(root)
Label4.place(relx=0.66,rely=0.41,height=21,width=57)
Label4.configure(text='minutes')
Label4.configure(anchor='w')

Button4=tk.Button(root)
Button4.place(relx=0.82,rely=0.4,height=29,width=55)
Button4.configure(text='Stop')
Button4.configure(command=stop)
Button4.configure(state=tk.DISABLED)

Label5=tk.Label(root)
Label5.place(relx=0.04,rely=0.54,height=33,width=85)
Label5.configure(font=('',18))
Label5.configure(text='MPSAS')
Label5.configure(anchor='w')

Entry3=tk.Entry(root)
Entry3.place(relx=0.3,rely=0.54,height=33,relwidth=0.66)
Entry3.configure(font=('',18))
Entry3.configure(width=316)
Entry3.configure(textvariable=mpsasVar)
Entry3.configure(state='readonly')

Label6=tk.Label(root)
Label6.place(relx=0.04,rely=0.68,height=21,width=41)
Label6.configure(text='NELM')
Label6.configure(anchor='w')

Entry4=tk.Entry(root)
Entry4.place(relx=0.3,rely=0.68,height=23,relwidth=0.66)
Entry4.configure(width=306)
Entry4.configure(textvariable=nelmVar)
Entry4.configure(state='readonly')

Label7=tk.Label(root)
Label7.place(relx=0.04,rely=0.78,height=21,width=88)
Label7.configure(text='Temperature')
Label7.configure(anchor='w')

Entry5=tk.Entry(root)
Entry5.place(relx=0.3,rely=0.78,height=23,relwidth=0.66)
Entry5.configure(width=296)
Entry5.configure(textvariable=tempVar)
Entry5.configure(state='readonly')

Label8=tk.Label(root)
Label8.place(relx=0.04,rely=0.88,height=21,width=37)
Label8.configure(text='Time')
Label8.configure(anchor='w')

Entry6=tk.Entry(root)
Entry6.place(relx=0.3,rely=0.88,height=23,relwidth=0.66)
Entry6.configure(width=306)
Entry6.configure(textvariable=timeVar)
Entry6.configure(state='readonly')


if os.path.isfile('sqm_config.txt'):
    f=open('sqm_config.txt','r')
    lines=f.readlines()
    f.close()
    if lines[0].strip() in TCombobox1['values']: portVar.set(lines[0].strip())
    baudVar.set(int(lines[1]))
    if len(lines[2].strip())>0: pathVar.set(lines[2].strip())
    else: pathVar.set('./')
    saveVar.set(lines[3].strip()=='True')
    dtVar.set(float(lines[4]))
    if len(lines)>5: midnightVar.set(lines[5].strip()=='True')
    else: midnightVar.set(True)       #old version of config file
    if len(lines)>6: uniVar.set(lines[6].strip()=='True')
    else: uniVar.set(False)       #old version of config file
else:
    saveVar.set(0)
    baudVar.set(115200)
    dtVar.set(1)


tk.mainloop()
