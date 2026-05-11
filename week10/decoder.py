from pathlib import Path

import numpy as np
import reedsolo
from scipy.fft import rfft, rfftfreq
from scipy.io import wavfile

# ===== 통신 파라미터 =====
SR = 48000  # 샘플레이트 (Hz)
UNIT_DUR = 0.1  # 심볼 1개 길이 (초)
SAMPLES_PER_UNIT = int(SR * UNIT_DUR)  # 4800 samples
FREQ_TOL = 20  # 주파수 매칭 허용 오차 (Hz)

# ===== Reed-Solomon (k=12, r=4) =====
K_DATA, R_PARITY = 12, 4
rs_codec = reedsolo.RSCodec(R_PARITY)

# ===== MFSK 주파수 매핑 =====
HEX_CHARS = "0123456789ABCDEF"
BASE_FREQ, DELTA = 512, 128


def build_freq_table():
    """심볼 → 반송 주파수 테이블 생성."""
    table = {"START": BASE_FREQ}
    for idx, ch in enumerate(HEX_CHARS, start=1):
        table[ch] = BASE_FREQ + DELTA + DELTA * idx
    table["END"] = BASE_FREQ + DELTA + DELTA * len(HEX_CHARS) + DELTA * 2
    return table


FREQ_MAP = build_freq_table()
FREQ_INDEX = sorted((f, s) for s, f in FREQ_MAP.items())


def peak_symbol(window):
    """윈도우의 최대 진폭 주파수에 해당하는 심볼 반환. 없으면 None."""
    spectrum = np.abs(rfft(window))
    freqs = rfftfreq(len(window), d=1.0 / SR)
    f_peak = freqs[np.argmax(spectrum)]
    for f_target, sym in FREQ_INDEX:
        if abs(f_peak - f_target) <= FREQ_TOL:
            return sym
    return None


def read_wav(path):
    """16-bit WAV을 float64 ndarray로 로드."""
    rate, data = wavfile.read(path)
    assert rate == SR, f"샘플레이트 불일치: {rate}Hz"
    if data.ndim > 1:  # stereo 대비
        data = data[:, 0]
    return data.astype(np.float64)


def find_start(samples, hop_sec=0.02):
    """슬라이딩 윈도우(20ms hop)로 START 톤 위치 탐색."""
    hop = int(SR * hop_sec)
    scan_end = len(samples) - SAMPLES_PER_UNIT
    for pos in range(0, scan_end, hop):
        if peak_symbol(samples[pos : pos + SAMPLES_PER_UNIT]) == "START":
            return pos
    return None


def read_payload(samples, start_pos):
    """START 톤(2 unit) 다음부터 END 톤까지 심볼 추출."""
    pos = start_pos + SAMPLES_PER_UNIT * 2
    chars, end_found = [], False
    while pos + SAMPLES_PER_UNIT <= len(samples):
        sym = peak_symbol(samples[pos : pos + SAMPLES_PER_UNIT])
        pos += SAMPLES_PER_UNIT
        if sym == "END":
            end_found = True
            break
        if sym is not None and sym != "START":
            chars.append(sym)
    return "".join(chars), end_found


def decode_file(path):
    print(f"\n[{path}]")
    try:
        audio = read_wav(path)
    except (AssertionError, FileNotFoundError) as exc:
        print(f"  파일 로딩 실패 → {exc}")
        return None

    start_at = find_start(audio)
    if start_at is None:
        print("  START 동기화 실패")
        return None
    print(f"  START 위치: sample #{start_at}")

    hex_payload, ended = read_payload(audio, start_at)
    print(f"  END 감지: {'O' if ended else 'X'}")
    print(f"  원본 hex: {hex_payload}")

    # 경계 노이즈로 홀수 길이 hex가 나올 수 있으니 보정
    if len(hex_payload) % 2:
        hex_payload = hex_payload[:-1]

    try:
        recovered = rs_codec.decode(bytes.fromhex(hex_payload))[0]
        password = recovered.decode("utf-8").rstrip("\x00")
        print(f"  >> 복원된 비밀번호: {password}")
        return password
    except reedsolo.ReedSolomonError:
        print("  RS 복원 실패 (오류 2바이트 초과)")
    except Exception as exc:
        print(f"  디코딩 예외: {exc}")
    return None


def main():
    sid, name = "202202599", "변경록"
    files = [f"{sid}_{name}_{i:02d}.wav" for i in range(1, 6)]
    passwords = list(filter(None, (decode_file(f) for f in files)))

    if passwords:
        out_path = Path(f"{sid}-{name}.txt")
        out_path.write_text("\n".join(passwords) + "\n", encoding="utf-8")
        print(f"\n총 {len(passwords)}개 비밀번호 저장 완료 → {out_path}")


if __name__ == "__main__":
    main()
