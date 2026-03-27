import socket

data = ""
print("Waiting for data...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # 핵심: 127.0.0.1이 아닌 0.0.0.0으로 바인딩하여 모든 IP의 접속 허용
    sock.bind(("0.0.0.0", 54321))
    sock.listen()

    conn, addr = sock.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            bit = conn.recv(1).decode("utf-8")
            if not bit:
                break
            print("BIT: " + bit)
            data += bit

n = 8
splitData = [data[i : i + n] for i in range(0, len(data), n)]
print("Data received: " + str(splitData))

character = ""
for x in splitData:
    splitInteger = int(x, 2)
    character += str(chr(splitInteger))

print("Message Converted: " + character)
