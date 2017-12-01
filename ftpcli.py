# Client 
from socket import *
import sys
import os

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
	
	# Keep receiving until all is received
	while len(recvBuff) < numBytes:
		
		# Attempt to receive bytes
		tmpBuff = sock.recv(numBytes)
		
		# The other side has closed the socket
		if not tmpBuff:
			break
			
		# Add the received bytes to the buffer
		recvBuff += tmpBuff
	
	return recvBuff

#gets server machine and port from command line
if len(sys.argv) < 3:
    print "USAGE python " + sys.argv[0] + "<SERVER MACHINE> <SERVER PORT>"
    exit(1)

serverName = sys.argv[1]
serverPort = int(sys.argv[2])
dataPort = 5020

# Create a TCP socket to connect with Sever
connSock = socket(AF_INET, SOCK_STREAM)

# Connect to the server
try:
	connSock.connect((serverName, serverPort))	
except:
	print "Error connecting to host"
	exit()

print "Waiting for ACK..."

check = recvAll(connSock, 1)
if (check == "a"):
    #send ACK back 
    connSock.send("a")
    print "Connection established"
else:
    print "Connection cannot be established"
    exit(1)

while True:
    c = raw_input("ftp> ")

    if c.strip() == 'quit':
        break
    elif c.strip() == 'ls':
		# Send command to the server
		connSock.send('l')
		
		# Generate ephemeral port and wait for
		# server to connect
        	dataSock = socket(AF_INET, SOCK_STREAM)
		flag = recvAll(connSock, 1)
		if flag == 'o':
			dataSock.connect((serverName, dataPort))
			#print "Now server is connected for data"
		else:
			print "cant connect"
				
		# Get the size of data from server
		dataSize = int(recvAll(dataSock, 10))
		
		# Get the data from the server
		dataList = recvAll(dataSock, dataSize)
		
		# Display the data received
		print dataList
		
		# Send ack to server signaling data received
		dataSock.send('a')
		
		# Close the socket
		dataSock.close()
    #gets first string/arg
    elif (c.split()[0] == "put"):
        if (len(c.split()) != 2):
            print "USAGE: put <filename>"
        elif not (os.path.exists(c.split()[1])):
            print "File does not exist"
        else:
            connSock.send("p")

            fileName = c.split()[1]
	    ephSocket = socket(AF_INET, SOCK_STREAM)
            flag = recvAll(connSock, 1)
            if flag == 'o':                
                ephSocket.connect((serverName, dataPort))
            else:
                print "Cant connect"

            #If ACK was received
            check = recvAll(ephSocket, 1)
            if (check == 'a'):
                fileObj = open(fileName, "r")
                numSent = 0
            
                #Obtain Filename size
                fileNameSize = str(len(fileName))
                while len(fileNameSize) < 10:
                    fileNameSize = "0" + fileNameSize

                fn = fileNameSize + fileName

                while True:
                    fileData = fileObj.read(65536)

                    if fileData:
                        dataSizeStr = str(len(fileData))

                        while len(dataSizeStr) < 10:
                            dataSizeStr = "0" + dataSizeStr

                        fileData = dataSizeStr + fileData

                        numSent = 0
                        fileData =  fn + fileData

                        while len(fileData) > numSent:
                            numSent += ephSocket.send(fileData[numSent:])
                    else:
                        break

                check = recvAll(ephSocket, 1)
                if (check == 'a'):
                    print "Sent ", numSent, "bytes."
                elif (check == 'e'):
                    msgsize = recvAll(ephSocket, 10)
                    msg = recvAll(ephSocket, int(msgsize))
                    print msg               

                ephSocket.close()
                fileObj.close()
            else:
                print "Connection cannot be establish with data channel"   
    elif (c.split()[0] == "get"):
        if (len(c.split()) != 2):
            print "USAGE: get <filename>"
        else: 
            fname = c.split()[1]
            fnameSize = str(len(fname))
            while len(fnameSize) < 10:
                fnameSize = "0" + fnameSize             
            msg = 'g' + fnameSize + fname
            
            numSent = 0 
            # Send the data!
            while len(msg) > numSent:
                numSent += connSock.send(msg[numSent:])

            ephSocket = socket(AF_INET, SOCK_STREAM)
            flag = recvAll(connSock, 1)
            if flag == 'o':
                # print "connecting to file transfer..."
                ephSocket.connect((serverName, dataPort))
            else: 
                print "something went wrong...."
            
            flag = recvAll(ephSocket, 1)
            if flag == 'e':
                #error message 
                msgSize = recvAll(ephSocket, 10)
                msg = recvAll(ephSocket, int(msgSize) )
                print msg 
            elif flag == 'a':
                fnameSize = recvAll(ephSocket, 10)
                fname = recvAll(ephSocket, int(fnameSize) )
                fsize = recvAll(ephSocket, 10)
                fileData = recvAll(ephSocket, int(fsize) )
                # print fname + " " + fileData
                # create file... 
            ephSocket.close() 
    else:
        print "Unknown command. Please use ls, get, put, or quit"


print "closing connection...."
connSock.send('q')
#wait for ACK back
flag = connSock.recv(1)
if(flag == 'q'):
    print "Success. Connection Ended."
else:
    print "Failed disconnecting."
connSock.close()

