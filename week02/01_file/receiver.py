import time

status = "0"
DATAFILE = "data"
SIGNALFILE = "signal"
gotData = False

with open(SIGNALFILE, "w") as f:
    f.write(str(1))
    f.close()

data = ""
print("Waiting for data...")

while True:
    time.sleep(0.01)
    with open(SIGNALFILE) as f:
        status = f.read()

    if status == "2":
        break

    if status == "0":
        bit = ""
        while not gotData:
            with open(DATAFILE) as f:
                bit = f.read()

            print("BIT: " + bit)
            if bit == "":
                gotData = False
            else:
                gotData = True

        data += bit
        with open(SIGNALFILE, "w") as f:
            f.write(str(1))
            f.close()

        gotData = False

n = 8
splitData = [data[i : i + n] for i in range(0, len(data), n)]
print("Data received: " + str(splitData))

character = ""
for x in splitData:
    splitInteger = int(x, 2)
    character += str(chr(splitInteger))

print("Message Converted: " + character)
