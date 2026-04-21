import math
import statistics
import struct

import pyaudio

# 물리 계층(L1)
INTMAX = 2 ** (32 - 1) - 1
FS = 48000
FREQ = 523.251  # C5

SEND_UNIT = 0.1  # 송신 규격: 100ms
SEND_CHUNK = int(FS * SEND_UNIT)

RECV_UNIT = 0.05  # 수신 규격: 50ms (위상 편이 방지를 위한 오버샘플링)
RECV_CHUNK = int(FS * RECV_UNIT)

# 최적화된 Noise Gate 임계값
MORSE_THRESHOLD = 15000000

# Hex-Morse Map
HEX_MORSE_MAP = {
    "0": "..-",
    "1": ".---",
    "2": "-..-",
    "3": "-...",
    "4": "----",
    "5": "-.--",
    "6": ".-..",
    "7": ".-.-",
    "8": "-.-.",
    "9": "---.",
    "A": "....-",
    "B": "--..",
    "C": ".....",
    "D": "--.-",
    "E": ".--.",
    "F": "...-",
}
REVERSE_MAP = {v: k for k, v in HEX_MORSE_MAP.items()}


def send_data():
    # 사용자 입력 파트
    user_input = input(
        "\n전송할 텍스트를 입력하세요 (한글, 이모지, 영어 모두 가능): "
    ).strip()

    # str => hex 변경 파트 (UTF-8 인코딩)
    byte_hex = user_input.encode("utf-8")
    hex_string = byte_hex.hex().upper()
    print(f"[디버그] 변환된 Hex String: {hex_string}")

    audio = []

    # Hex String => 모스부호 소리 변환
    for char_idx, char in enumerate(hex_string):
        morse = HEX_MORSE_MAP.get(char, "")

        for symbol_idx, symbol in enumerate(morse):
            duration = 1 if symbol == "." else 3
            # 소리 생성 (1 unit or 3 units)
            for i in range(duration * SEND_CHUNK):
                audio.append(int(INTMAX * math.sin(2 * math.pi * FREQ * (i / FS))))
            # 기호 간 묵음 (1 unit)
            if symbol_idx < len(morse) - 1:
                audio.extend([0] * SEND_CHUNK)

        # 16진수 문자 간 묵음 (3 units)
        # (띄어쓰기조차 UTF-8로는 '20'이라는 Hex값으로 변환되므로 7 unit 공백이 불필요합니다)
        if char_idx < len(hex_string) - 1:
            audio.extend([0] * (3 * SEND_CHUNK))

    # PyAudio 재생 (송신)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt32, channels=1, rate=FS, output=True)

    print("\n[송신 중... 스피커의 소리를 마이크에 가까이 하세요]")
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
    # 끝부분의 타임아웃용 묵음 제거
    sequence = sequence[:-max_unseen]
    morse_symbols = []
    count = 1

    # 1과 0의 배열을 모스 부호(. - |)로 디코딩
    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i - 1]:
            count += 1
        else:
            if sequence[i - 1] == 1:
                if count <= 3:
                    morse_symbols.append(".")  # 50~150ms -> 점
                else:
                    morse_symbols.append("-")  # 200ms 이상 -> 선
            else:
                if count >= 3:
                    morse_symbols.append("|")  # 150ms 이상 -> 문자 구분
            count = 1

    if sequence and sequence[-1] == 1:
        if count <= 3:
            morse_symbols.append(".")
        else:
            morse_symbols.append("-")

    raw_morse = "".join(morse_symbols)
    print(f"\n인식된 모스 기호: {raw_morse.replace('|', ' ')}")

    # 모스 부호를 16진수 문자열(Hex String)로 변환
    hex_string = ""
    chars = raw_morse.split("|")
    for char in chars:
        hex_string += REVERSE_MAP.get(char, "")  # 매핑되지 않는 쓰레기값 무시

    print(f"해독된 Hex String: {hex_string}")

    # Hex String => str 사용자 출력 변환 파트 (UTF-8 디코딩)
    try:
        # 노이즈로 인해 16진수 개수가 홀수개가 될 경우를 대비해 짝수개로 맞춤
        if len(hex_string) % 2 != 0:
            hex_string = hex_string[:-1]

        client_byte_hex = bytes.fromhex(hex_string)
        # errors='replace'를 통해 노이즈로 깨진 문자가 있어도 프로그램이 죽지 않도록 방어
        client_output = client_byte_hex.decode("utf-8", errors="replace")
        print(f"★ 최종 해독 원본 문자열: {client_output} ★\n")
    except ValueError as e:
        print(
            f"[해독 실패] 정상적인 16진수 문자열이 수신되지 않았습니다. (에러: {e})\n"
        )


def main():
    while True:
        print("=" * 45)
        print("Unicode over Sound with Noise")
        print("[1] Send Unicode over sound (play)")
        print("[2] Receive Unicode over sound (record)")
        print("[q] Exit")
        print("=" * 45)
        select = input("Select menu: ").strip().lower()
        if select == "1":
            send_data()
        elif select == "2":
            receive_data()
        elif select == "q":
            print("Terminating...")
            break


if __name__ == "__main__":
    main()
