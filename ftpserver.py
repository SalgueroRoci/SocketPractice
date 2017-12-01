# Server ftp side program 
# Reference code for file_size and file_exist functions:
# https://stackoverflow.com/questions/6591931/getting-file-size-in-python
# https://stackoverflow.com/questions/20517785/python-except-oserror-e-no-longer-working-in-3-3-3

import socket
import commands
import sys

# ************************************************
# Receives the specified number of bytes
# from the specified socket
# @param sock - the socket from which to receive
# @param numBytes - the number of bytes to receive
# @return - the bytes received
# *************************************************
def recvAll(sock, numBytes):

    # The buffer
    recvBuff = ""
    
    # The temporary buffer
    tmpBuff = ""
    
    # Keep receiving till all is received
    while len(recvBuff) < numBytes:
        
        # Attempt to receive bytes
        tmpBuff =  sock.recv(numBytes)
        
        # The other side has closed the socket
        if not tmpBuff:
            break
        
        # Add the received bytes to the buffer
        recvBuff += tmpBuff
    
    return recvBuff

def file_size(fname):
        import os
        statinfo = os.stat(fname)
        return statinfo.st_size

def file_exist(fname):
    import os.path
    return os.path.isfile(fname) 

#main start =================================
TCP_IP = ''
# SERVER_PORT = 5021
FILE_TRANS_PORT = 5020
BUFFER_SIZE = 2048  



# Command line checks
if len(sys.argv) != 2:
    print "USAGE python " + sys.argv[0] + " <SERVER PORT>"
    exit()
   
# Server port
tempPort = sys.argv[1]
SERVER_PORT = int(tempPort)

#create socket for server 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, SERVER_PORT))
s.listen(1)

f = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
f.bind((TCP_IP, FILE_TRANS_PORT))


print 'Waiting to recieve connections'

while 1:
    clientSocket, addr = s.accept()
    #Get connection from client 
    print 'Connection address:', addr , clientSocket.getsockname()[0], clientSocket.getsockname()[1]   
    #send connection ACK to client 
    clientSocket.send('a')
    # wait for ACK from client then start ftp program 
    connACK = recvAll(clientSocket, 1)

    if (connACK == 'a'):
        print "CONNECTION ESTAB. SUCCESS"

        #start listening to client commands 
        header = ''
        while header != 'q':
            header = recvAll(clientSocket, 1)
            #check if connection closed 
            if not header: break 
            print "recieved " , header 

            if header == 'l':
                print "create new socket"
                f.listen(1)

                clientSocket.send('o')
                fileS, addr2 = f.accept()
                
                print "connected" , f.getsockname()[1]

                #get string and length
                lpacket = ''
                for line in commands.getstatusoutput('ls -l'):
                    lpacket += str(line)

                #get packet length 
                packetLength = str(len(lpacket))

                #make length part to be 10 bytes 
                while len(packetLength) < 10:
                    packetLength = "0" + packetLength
                
                lpacket = packetLength + lpacket

                # The number of bytes sent
                numSent = 0
                
                # Send the data!
                while len(lpacket) > numSent:
                    numSent += fileS.send(lpacket[numSent:])
                
                print "sent ", lpacket
                
                #wait for ack back 
                ackL = recvAll(fileS, 1)
                if (ackL == 'a'):
                    print "Success"
                else:
                    print "Failure"

                fileS.close() 
            elif header == 'p':
                print "create new socket"  
              
                f.listen(1)
                clientSocket.send('o')
                fileS, addr2 = f.accept()
                
                print "connected" , f.getsockname()[1]

                #send connection ack 
                fileS.send("a") 

                # retrieve the data sent by client 
                # flag = recvAll(fileS, 1) 
                fnameSize = recvAll(fileS, 10)
                fname = recvAll(fileS, int(fnameSize) )
                fsize = recvAll(fileS, 10)
                data = recvAll(fileS, int(fsize))

                #check if file exists 
                if not file_exist(fname):
                    #create the file and add to server folders 
                    fileObj = open(fname, "w")

                    fileObj.write(data)

                    #close file 
                    fileObj.close()

                    # Send the ACK  
                    ackP = 'a' 
                    numSent = 0                 
                    while len(ackP) > numSent:
                        numSent += fileS.send(ackP[numSent:])
                    
                    print "Successful PUT"
                else:
                    #file exists
                    data = 'e' 
                    msg = "File already exist. " + fname
                    msgLeng = str(len(msg))

                    #make length part to be 10 bytes 
                    while len(msgLeng) < 10:
                        msgLeng = "0" + msgLeng

                    data = data + msgLeng + msg 

                    numSent = 0 
                    # Send the data!
                    while len(data) > numSent:
                        numSent += fileS.send(data[numSent:])
                    
                    print "Failure. ", msg
                fileS.close()
            elif header == 'g':
		print "create new socket for get"
                #get file name size (10 bytes)
                fnameSize = recvAll(clientSocket, 10)

                #get file name 
                fname = recvAll(clientSocket, int(fnameSize))
		
                f.listen(1)		
                clientSocket.send('o')
                fileS, addr2 = f.accept()

                #check if file exist 
                if not file_exist(fname): 
                    msg = "File does not exist. " + fname
                    msgLeng = str(len(msg))

                    #make length part to be 10 bytes 
                    while len(msgLeng) < 10:
                        msgLeng = "0" + msgLeng

                    data = 'e' + msgLeng + msg 
                    
                    numSent = 0
                    # Send the data!
                    while len(data) > numSent:
                        numSent += fileS.send(data[numSent:])
                    
                    print "Message sent: " , msg                   
                else: 
                    #open file read only 
                    fileObj = open(fname, "r")
                    fsize = 0 
                    #save size and data
                    try:
                        fsize = file_size(fname)
                    except OSError, e:
                        print e.errno == errno
                        fsize = 0
                    fsize = str(fsize)
                    #make length part to be 10 bytes 
                    while len(fsize) < 10:
                        fsize = "0" + fsize

                    #get the data
                    fileData = fileObj.read(int(fsize) )

                    #close file 
                    fileObj.close() 

                    #packet =  file name size + file name + file size + data
                    packet = 'a' + fnameSize + fname + fsize + fileData 
                    
                    numSent = 0 
                    # Send the data!
                    while len(packet) > numSent:
                        numSent += fileS.send(packet[numSent:])
                    
                    print "file sent ", fname 
                print "closing file connection..."
                fileS.close()                    
    else: 
        print "Connection Failed. ", connACK     


    #send ACKquit back 
    sendQuit = 'q' 
    clientSocket.send(sendQuit)       
    print "closing.... ", addr, " message sent ", sendQuit 
    #closing process 
    clientSocket.close()
    print "SUCCESS"
