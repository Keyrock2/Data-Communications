import math
import struct
import wave

# 설정 값
INTMAX = 1000000000  # 소리 크기 (32-bit 정수 범위 내)


def morse2audio(morse):
    t = 0.5  # 기본 단위 시간 (0.5초)
    fs = 48000  # 샘플링 레이트 (1초당 데이터 개수)
    f = 261.626  # 주파수 (C4 도)
    audio = []

    for m in morse:
        if m == ".":
            # 1단위 시간 동안 소리 생성
            for i in range(int(t * fs * 1)):
                audio.append(int(INTMAX * math.sin(2 * math.pi * f * (i / fs))))
        elif m == "-":
            # 3단위 시간 동안 소리 생성
            for i in range(int(t * fs * 3)):
                audio.append(int(INTMAX * math.sin(2 * math.pi * f * (i / fs))))

        # 부호가 끝난 후 항상 1단위 시간만큼 무음(0) 추가
        for i in range(int(t * fs * 1)):
            audio.append(0)

    return audio


def audio2file(audio, filename):
    with wave.open(filename, "wb") as w:
        w.setnchannels(1)  # 모노
        w.setsampwidth(4)  # 32비트 (4바이트)
        w.setframerate(48000)  # 48kHz

        # 데이터를 바이너리로 변환하여 기록
        for a in audio:
            w.writeframes(struct.pack("<i", a))  # '<i'는 리틀 엔디안 32비트 정수


# 실행부
morse_input = "... --- ..."  # SOS
audio_data = morse2audio(morse_input)
audio2file(audio_data, "morse_signal.wav")

print("morse_signal.wav 파일이 생성되었습니다.")
