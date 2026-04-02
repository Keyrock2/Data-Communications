import math
import struct
import wave

# 모스 부호 딕셔너리
english = {
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
}
number = {
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


def generate_morse_wav(text, filename):
    INTMAX = 2 ** (32 - 1) - 1
    unit_t = 0.1  # unit = 100ms
    fs = 48000  # Sample rate
    f = 523.251  # Frequency

    unit_samples = int(unit_t * fs)
    audio = []

    text = text.upper()

    for word_idx, word in enumerate(text.split(" ")):
        for char_idx, char in enumerate(word):
            # 문자 -> 모스 부호 변환
            morse = english.get(char, "") if char.isalpha() else number.get(char, "")

            for symbol_idx, symbol in enumerate(morse):
                # 소리 추가
                duration = 1 if symbol == "." else 3
                for i in range(duration * unit_samples):
                    audio.append(int(INTMAX * math.sin(2 * math.pi * f * (i / fs))))

                # 기호 간 간격 (intra-character gap): 1 unit 묶음
                if symbol_idx < len(morse) - 1:
                    audio.extend([0] * (1 * unit_samples))

            # 문자 간 간격 (inter-character gap): 3 units 묶음
            if char_idx < len(word) - 1:
                audio.extend([0] * (3 * unit_samples))

        # 단어 간 간격 (inter-word gap): 7 units 묵음
        if word_idx < len(text.split(" ")) - 1:
            audio.extend([0] * (7 * unit_samples))

    # WAV 파일 기록
    with wave.open(filename, "wb") as w:
        w.setnchannels(1)  # Mono
        w.setsampwidth(4)  # 32bit
        w.setframerate(fs)
        for a in audio:
            w.writeframes(struct.pack("<i", a))
    print(f"WAV 생성 완료: {filename}")


my_text = "CNU CSE 202202599 BYUNKYUNGROCK"
my_filename = "202202599_변경록.wav"

generate_morse_wav(my_text, my_filename)
