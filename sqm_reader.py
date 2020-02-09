import time
import serial

port='COM9'
t0=0
dt=60

com=serial.Serial(port)
com.baudrate=115200
print('Init')
time.sleep(10)
print('Init finished')

i=0
loop=True
while loop:
    if time.time()-t0>dt:
        t0=time.time()
        com.write(b'rx\r')
        print('reading')
        time.sleep(5)
        sqm=com.readline().decode().strip()
        ##        while not ans==b'\n':
##            print(ans)
##            sqm+=ans
##            ans=str(com.read())
##            print('reading')
##            break
        print('finished')
        #sqm=com.read()       #r,-09.42m,0000005915Hz,0000000000c,0000000.000s, 027.0C -> r,mpsas,freq,period,per,temp 
        cas=time.strftime('%Y_%m_%d %H:%M:%S',time.localtime(t0))
        print(cas,sqm)
        i+=1
        loop=(i<3)
    time.sleep(1)
com.close() 
    
