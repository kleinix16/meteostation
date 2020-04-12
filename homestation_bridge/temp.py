'''
UART communication on Raspberry Pi using Pyhton
http://www.electronicwings.com
'''
import serial
import time 

ser = serial.Serial ("/dev/ttyAMA0", 9600)    #Open port with baud rate
# while True:
#     received_data = ser.read()              #read serial port
#     sleep(0.03)
#     data_left = ser.inWaiting()             #check for remaining byte
#     received_data += ser.read(data_left)
#     print (received_data)                   #print received data
#     ser.write(received_data)                #transmit data serially 
counter = 0
print(ser.portstr)

while 1:
    print('Write counter: %d \n'%(counter))
    #send data via serial port
    ser.write("012345688902341".encode())

    time.sleep(5)
    counter += 1

