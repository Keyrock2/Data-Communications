# 변환용 데이터
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
    " ": "/",  # 공백 구분용
}


# 분석 대상 함수
def text2morse(text):
    text = text.upper()  # 소문자 입력 방지 (모스 부호는 대문자 기준)
    morse = ""

    for t in text:  # 입력받은 문장을 한 글자씩 꺼냄 (예: 'H', 'E', 'L'...)
        # 알파벳 딕셔너리에서 검색
        for key, value in english.items():
            if t == key:
                morse = (
                    morse + value + " "
                )  # 가독성을 위해 한 글자 끝날 때마다 공백 추가

        # 숫자 딕셔너리에서 검색
        for key, value in number.items():
            if t == key:
                morse = morse + value + " "

    return morse.strip()  # 마지막에 붙은 불필요한 공백 제거


# 실행 테스트
input_text = "SOS 112"
result = text2morse(input_text)

print(f"입력: {input_text}")
print(f"변환 결과: {result}")
