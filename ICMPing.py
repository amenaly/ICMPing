from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

#keep two blank lines

#function to calculate the checksum to string
def checksum(string):
    # intiliaze checksum
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    #swap bytes to have it match the data
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

#recieve the ping from the socket
def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    #setting up the ms delay
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)

        if not whatReady[0]:  # Timeout
            return "Request timed out."
        #when we get the delay we set it to this
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Get the ICMP Header from packet
        header = recPacket[20:28]
        pingtype, code, mychecksum, pID, sNum = struct.unpack("bbHHh", header)

        #print("The header received in the ICMP reply is ", type, code, checksum, pID, sNum)
        if type != 8 and pID == ID: #filters out the echo request you sent
            tsize = struct.calcsize("d") #how many bytes sent
            timedata = struct.unpack("d", recPacket[28:28 + tsize])[0]
            # use to round the time in ms
            result = round((timeReceived - timedata)*1000)
            # convert the delay into seconds and returns that result to ping function
            return result, tsize

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."

# send ping to dest addr


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # make a dummy header with 0 checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff

    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))

# returns the delay in ms


def doOnePing(destAddr, timeout):
    # sends ping to destAddr given and returns the delay in ms
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    # Return the current process i
    myID = os.getpid() & 0xFFFF
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay
# sends ping to destaddr and display the results


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Send ping requests to a server separated by a second
    # also limit the range to not be a endless loop
    for i in range(0, 10):
        # set it for a limit of 10 pings before finishing
        delay, tsize = doOnePing(dest, timeout)

        print("Received from " + dest + ": bytes= " + str(tsize) + " delay= " + str(delay)+"ms")
        time.sleep(1)
        # one-second delay
    # have to keep outside the for loop
    return


#ping("127.0.0.1")
#ping("localhost")
#ping("amazon.com")
#ping("google.com")
ping("uni-freiburg.de") #University of Freiburg in Germany
#ping("en.snu.ac.kr") #Seoul National University in South Korea
