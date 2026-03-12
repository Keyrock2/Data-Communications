import socket

data = ""
print("Waiting for data...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 54321))
    sock.listen()

    conn, addr = sock.accept()
    with conn:
        while True:
            bit = conn.recv(1).decode()
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
