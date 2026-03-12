import socket
import time

hasSentComplete = 0

input_string = input("Input string: ")
bit_msg = "".join([bin(ord(ch))[2:].zfill(8) for ch in input_string])
i = 0

print("Bit string to send: " + str(bit_msg))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect(("127.0.0.1", 54321))

    while hasSentComplete == 0:
        time.sleep(0.01)
        print("Loop: {}/{}".format(str(i), str(len(bit_msg))))
        print("Progress: {}/100".format(str(int(i / len(bit_msg) * 100))))

        sock.sendall(bit_msg[i].encode())

        i += 1
        if i == len(bit_msg):
            hasSentComplete = 1
            print("Data sent: " + str(bit_msg))
