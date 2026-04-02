import math
import statistics
import struct
import wave

# 모스 부호 역방향 딕셔너리 (모스부호 -> 문자)
english = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
}
number = {
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    "-----": "0",
}

# 두 딕셔너리 병합
morse_to_char = {**english, **number}


def decode_morse_wav(filename):
    with wave.open(filename, "rb") as w:
        framerate = w.getframerate()
        frames = w.getnframes()
        audio = []
        for i in range(frames):
            frame = w.readframes(1)
            audio.append(struct.unpack("<i", frame)[0])

    unit_samples = int(0.1 * framerate)  # 1 unit = 0.1s
    chunks = math.ceil(len(audio) / unit_samples)

    # 각 유닛별로 신호(1)인지 묵음(0)인지 판별
    signal_sequence = []
    for i in range(chunks):
        chunk_data = audio[i * unit_samples : (i + 1) * unit_samples]
        if len(chunk_data) < unit_samples // 2:  # 자투리 무시
            break
        stdev = statistics.stdev(chunk_data)
        signal_sequence.append(1 if stdev > 10000 else 0)

    # 연속된 1과 0의 길이를 파악하여 모스 부호 도출
    morse_symbols = []
    count = 1
    for i in range(1, len(signal_sequence)):
        if signal_sequence[i] == signal_sequence[i - 1]:
            count += 1
        else:
            if signal_sequence[i - 1] == 1:  # 소리 구간 종료
                if count == 1:
                    morse_symbols.append(".")
                elif count == 3:
                    morse_symbols.append("-")
            else:  # 묵음 구간 종료
                if count == 3:
                    morse_symbols.append("|")  # 문자 구분
                elif count >= 7:
                    morse_symbols.append("||")  # 단어 구분
            count = 1

    # 마지막 시퀀스 처리
    if signal_sequence[-1] == 1:
        if count == 1:
            morse_symbols.append(".")
        elif count == 3:
            morse_symbols.append("-")

    # 도출된 모스 부호를 문자열로 변환
    decoded_text = ""
    words = "".join(morse_symbols).split("||")
    for word in words:
        chars = word.split("|")
        for char in chars:
            if char in morse_to_char:
                decoded_text += morse_to_char[char]
        decoded_text += " "

    return decoded_text.strip()


# 과제 파일명 입력
target_file = "output_202202599_변경록.wav"
result_text = decode_morse_wav(target_file)

print(f"해독된 텍스트: {result_text}")

# txt 파일로 저장
with open("202202599_변경록.txt", "w") as f:
    f.write(result_text)
print("텍스트 파일 저장 완료!")
