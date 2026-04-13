import math
import re
import statistics
import struct

import pyaudio

INTMAX = 2 ** (32 - 1) - 1
FS = 48000
FREQ = 523.251  # C5

# 송수신 동기화를 위한 오버샘플링 설정
SEND_UNIT = 0.1  # 송신 규격: 100ms
SEND_CHUNK = int(FS * SEND_UNIT)  # 4800 샘플

RECV_UNIT = 0.05  # 수신 규격: 50ms 위상 편이 방지를 위해 2배 빠르게 샘플링
RECV_CHUNK = int(FS * RECV_UNIT)  # 2400 샘플

# 우리 집에 최적화한 임계값
MORSE_THRESHOLD = 15000000

MORSE_MAP = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
}
REVERSE_MAP = {v: k for k, v in MORSE_MAP.items()}


def send_data():
    while True:
        print("\nType some text (only English and Number)")
        text = input("User input: ").strip().upper()
        if re.match(r"^[A-Z0-9 ]+$", text):
            break
        print("Invalid input! 영문자와 숫자, 공백만 입력하세요.")

    audio = []

    for char_idx, char in enumerate(text):
        if char == " ":
            audio.extend([0] * (7 * SEND_CHUNK))
            continue

        morse = MORSE_MAP.get(char, "")
        for symbol_idx, symbol in enumerate(morse):
            duration = 1 if symbol == "." else 3
            for i in range(duration * SEND_CHUNK):
                audio.append(int(INTMAX * math.sin(2 * math.pi * FREQ * (i / FS))))
            if symbol_idx < len(morse) - 1:
                audio.extend([0] * SEND_CHUNK)

        if char_idx < len(text) - 1 and text[char_idx + 1] != " ":
            audio.extend([0] * (3 * SEND_CHUNK))

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt32, channels=1, rate=FS, output=True)

    print("\n[송신 중...]")
    for i in range(0, len(audio), SEND_CHUNK):
        chunk_data = audio[i : i + SEND_CHUNK]
        stream.write(struct.pack("<" + ("i" * len(chunk_data)), *chunk_data))

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("[송신 완료]\n")


def receive_data():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt32,
        channels=1,
        rate=FS,
        input=True,
        frames_per_buffer=RECV_CHUNK,
    )

    print("\n[수신 대기 중... 모스부호 소리를 들려주세요]")
    print("(소리가 끝나고 3초간 묵음이 지속되면 자동 종료 및 해석됩니다)\n")

    tuning = True
    unseen_chunks = 0
    UNSEEN_THRESHOLD = 3.0
    max_unseen = int(UNSEEN_THRESHOLD / RECV_UNIT)  # 50ms 기준 60 청크 = 3초

    signal_sequence = []

    try:
        while True:
            data = stream.read(RECV_CHUNK, exception_on_overflow=False)
            unpacked_data = struct.unpack("<" + ("i" * RECV_CHUNK), data)

            stdev = statistics.stdev(unpacked_data)
            is_signal = stdev >= MORSE_THRESHOLD

            if tuning:
                if is_signal:
                    tuning = False
                    print("\n[데이터 수신 시작됨]")
                else:
                    continue

            if is_signal:
                signal_sequence.append(1)
                unseen_chunks = 0
                print("■", end="", flush=True)
            else:
                signal_sequence.append(0)
                unseen_chunks += 1
                print("□", end="", flush=True)

                if unseen_chunks >= max_unseen:
                    print("\n\n[3초간 묵음 감지. 수신을 자동 종료합니다.]")
                    break

    except KeyboardInterrupt:
        pass

    stream.stop_stream()
    stream.close()
    p.terminate()

    decode_signal(signal_sequence, max_unseen)


def decode_signal(sequence, max_unseen):
    sequence = sequence[:-max_unseen]
    morse_symbols = []
    count = 1

    # 50ms 단위로 세밀하게 디코딩 로직 조정
    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i - 1]:
            count += 1
        else:
            if sequence[i - 1] == 1:
                if count <= 3:  # 50~150ms -> 점
                    morse_symbols.append(".")
                else:  # 200ms 이상 -> 선
                    morse_symbols.append("-")
            else:
                if 3 <= count <= 7:  # 150~350ms -> 문자 간격
                    morse_symbols.append("|")
                elif count >= 8:  # 400ms 이상 -> 단어 간격
                    morse_symbols.append("||")
            count = 1

    if sequence and sequence[-1] == 1:
        if count <= 3:
            morse_symbols.append(".")
        else:
            morse_symbols.append("-")

    raw_morse = "".join(morse_symbols)
    print(f"\n인식된 모스 기호: {raw_morse.replace('|', ' ').replace('||', ' / ')}")

    decoded_text = ""
    words = raw_morse.split("||")
    for word in words:
        chars = word.split("|")
        for char in chars:
            decoded_text += REVERSE_MAP.get(char, "?")
        decoded_text += " "

    print(f"최종 해독 원본 문자열: {decoded_text.strip()}\n")


def main():
    while True:
        print("=" * 45)
        print("Morse Code over Sound with Noise")
        print("[1] Send morse code over sound (play)")
        print("[2] Receive morse code over sound (record)")
        print("[q] Exit")
        print("=" * 45)
        select = input("Select menu: ").strip().upper()
        if select == "1":
            send_data()
        elif select == "2":
            receive_data()
        elif select == "Q":
            print("Terminating...")
            break


if __name__ == "__main__":
    main()
