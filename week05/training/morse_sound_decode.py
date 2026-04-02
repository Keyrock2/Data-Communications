import math
import statistics
import struct
import wave

# 이전 연습에서 사용한 설정값들
INTMAX = 1000000000
FS = 48000
T = 0.5


def file2morse(filename):
    with wave.open(filename, "rb") as w:
        audio = []
        frames = w.getnframes()

        # 파일에서 바이너리 데이터를 읽어 정수로 변환 (Unpacking)
        for i in range(frames):
            frame = w.readframes(1)
            # '<i'는 32비트 정수(4바이트)를 의미합니다.
            audio.append(struct.unpack("<i", frame)[0])

    morse = ""
    unit = int(T * FS)  # 0.5초에 해당하는 샘플 개수 (24,000개)

    # Unit 단위로 순회하며 표준 편차 계산
    # (i-1)*unit 부터 i*unit 까지가 0.5초 구간입니다.
    for i in range(1, math.ceil(len(audio) / unit) + 1):
        segment = audio[(i - 1) * unit : i * unit]

        if len(segment) < 100:  # 너무 짧은 구간은 무시
            continue

        stdev = statistics.stdev(segment)

        # 표준 편차가 10,000보다 크면 소리가 있는 것으로 판단
        if stdev > 10000:
            morse = morse + "."
        else:
            morse = morse + " "

    # 규칙에 따른 문자 치환
    # 0.5초 단위로 읽었으므로 1.5초(0.5*3) 소리는 '...'으로 표시됨 -> 이를 '-'로 변경
    morse = morse.replace("...", "-")
    return morse


# 테스트 실행
try:
    decoded_morse = file2morse("morse_signal.wav")
    print(f"분석된 모스 부호: {decoded_morse}")
except FileNotFoundError:
    print("먼저 연습 3의 코드를 실행하여 'morse_signal.wav' 파일을 생성해주세요!")
