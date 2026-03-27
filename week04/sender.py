import socket
import time

hasSentComplete = 0

input_string = input("Input string: ")
bit_msg = "".join([bin(ord(ch))[2:].zfill(8) for ch in input_string])
i = 0

print("Bit string to send: " + str(bit_msg))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # 핵심: 방금 ifconfig로 찾은 receiver의 IP를 입력하세요! (예: inet 172.17.0.3)
    TARGET_IP = "172.17.0.3"
    sock.connect((TARGET_IP, 54321))

    while hasSentComplete == 0:
        time.sleep(0.01)
        print("Loop: {}/{}".format(str(i), str(len(bit_msg))))
        sock.send(bytes(bit_msg[i], "utf-8"))
        i += 1
        if i == len(bit_msg):
            hasSentComplete = 1
            print("Data sent: " + str(bit_msg))
