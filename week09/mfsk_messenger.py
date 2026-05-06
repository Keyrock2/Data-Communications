import math
import statistics
import struct

import numpy as np
import pyaudio
from scipy.fftpack import fft, fftfreq

MAX_AMP = 2**31 - 1
SAMPLE_RATE = 48000
TIME_PER_UNIT = 0.1
BLOCK_LEN = int(SAMPLE_RATE * TIME_PER_UNIT)

GAP_TIME = 0.02
GAP_SAMPLES = int(SAMPLE_RATE * GAP_TIME)

HOP = BLOCK_LEN // 4
STABLE_NEEDED = 3

BASE_FREQ = 1000
FREQ_GAP = 100
HEX_CHARS = list("0123456789ABCDEF")
TOLERANCE_HZ = 25

MFSK_FREQ_MAP = {"BEGIN": BASE_FREQ}
for idx, h_char in enumerate(HEX_CHARS):
    MFSK_FREQ_MAP[h_char] = BASE_FREQ + FREQ_GAP * (idx + 2)
MFSK_FREQ_MAP["STOP"] = BASE_FREQ + FREQ_GAP * (len(HEX_CHARS) + 3)

NOISE_CUTOFF_VAL = 15_000_000


def create_sine_wave(target_freq, duration_units):
    """주어진 주파수의 사인파 샘플 배열 생성"""
    total_samples = int(duration_units * BLOCK_LEN)
    return [
        int(MAX_AMP * math.sin(2 * math.pi * target_freq * (n / SAMPLE_RATE)))
        for n in range(total_samples)
    ]


def extract_peak_frequency_symbol(chunk_arr):
    """FFT로 최고 진폭 주파수를 찾아 매핑된 심볼 반환"""
    freq_axis = fftfreq(len(chunk_arr), d=1 / SAMPLE_RATE)
    fft_values = fft(chunk_arr)
    half = len(chunk_arr) // 2
    peak_idx = int(np.argmax(np.abs(fft_values[:half])))
    peak_hz = freq_axis[peak_idx]

    for sym, f_val in MFSK_FREQ_MAP.items():
        if f_val - TOLERANCE_HZ <= peak_hz <= f_val + TOLERANCE_HZ:
            return sym
    return None


def calibrate_noise_floor(in_stream, calib_seconds=1.0):
    """배경 소음을 측정해 노이즈 임계값 자동 설정"""
    print(f"[*] {calib_seconds:.1f}초간 배경 소음 측정 중... 조용히 해주세요.")
    samples = []
    n_blocks = max(1, int(calib_seconds / TIME_PER_UNIT))
    for _ in range(n_blocks):
        raw = in_stream.read(BLOCK_LEN, exception_on_overflow=False)
        samples.extend(struct.unpack("<" + "i" * BLOCK_LEN, raw))
    bg_std = statistics.stdev(samples)
    cutoff = max(bg_std * 4, 5_000_000)
    print(f"[*] 배경 stdev = {bg_std:,.0f}  →  cutoff = {cutoff:,.0f}")
    return cutoff


def transmit_mfsk_signal():
    msg = input("\n[입력] 보낼 메시지 (한글/이모지 가능): ").strip()
    if not msg:
        print("[!] 빈 메시지입니다.")
        return

    encoded_hex_str = msg.encode("utf-8").hex().upper()
    print(f"[*] 인코딩된 HEX 데이터: {encoded_hex_str}")

    sound_payload = []

    sound_payload.extend(create_sine_wave(MFSK_FREQ_MAP["BEGIN"], 2))
    sound_payload.extend([0] * GAP_SAMPLES)

    for hex_char in encoded_hex_str:
        sound_payload.extend(create_sine_wave(MFSK_FREQ_MAP[hex_char], 1))
        sound_payload.extend([0] * GAP_SAMPLES)

    sound_payload.extend(create_sine_wave(MFSK_FREQ_MAP["STOP"], 2))

    pa = pyaudio.PyAudio()
    out_stream = pa.open(
        format=pyaudio.paInt32, channels=1, rate=SAMPLE_RATE, output=True
    )

    print("\n>>> 사운드 전송 시작 — 마이크와 가까이 두세요 <<<")
    for chunk_start in range(0, len(sound_payload), BLOCK_LEN):
        slice_data = sound_payload[chunk_start : chunk_start + BLOCK_LEN]
        packed_bytes = struct.pack("<" + ("i" * len(slice_data)), *slice_data)
        out_stream.write(packed_bytes)

    out_stream.stop_stream()
    out_stream.close()
    pa.terminate()
    print(">>> 사운드 전송 완료 <<<\n")


def capture_and_decode_mfsk():
    global NOISE_CUTOFF_VAL

    pa = pyaudio.PyAudio()
    in_stream = pa.open(
        format=pyaudio.paInt32,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=BLOCK_LEN,
    )

    NOISE_CUTOFF_VAL = calibrate_noise_floor(in_stream)

    print("\n<<< 수신 대기 중... MFSK 사운드를 재생해주세요 >>>")

    ring = []

    def read_hop():
        raw = in_stream.read(HOP, exception_on_overflow=False)
        ring.extend(struct.unpack("<" + "i" * HOP, raw))
        if len(ring) > BLOCK_LEN * 4:
            del ring[: -BLOCK_LEN * 2]

    def current_symbol():
        """최근 BLOCK_LEN 샘플로 심볼 추정"""
        if len(ring) < BLOCK_LEN:
            return None, 0.0
        win = ring[-BLOCK_LEN:]
        amp = statistics.stdev(win)
        if amp < NOISE_CUTOFF_VAL:
            return None, amp
        return extract_peak_frequency_symbol(win), amp

    while True:
        read_hop()
        sym, _ = current_symbol()
        if sym == "BEGIN":
            print("[*] BEGIN 진입 감지. 데이터 대기...")
            break

    collected = ""
    stop_cnt = 0
    last_seen = None
    stable_cnt = 0

    while True:
        read_hop()
        sym, _ = current_symbol()

        if sym is None:
            last_seen = None
            stable_cnt = 0
            continue

        if sym == "BEGIN":
            last_seen = "BEGIN"
            stable_cnt = 0
            continue

        if sym == "STOP":
            stop_cnt = stop_cnt + 1 if last_seen == "STOP" else 1
            last_seen = "STOP"
            if stop_cnt >= STABLE_NEEDED:
                print("\n[*] STOP 안정 감지 — 수신 종료")
                break
            continue

        if sym == last_seen:
            stable_cnt += 1
        else:
            last_seen = sym
            stable_cnt = 1
            stop_cnt = 0

        if stable_cnt == STABLE_NEEDED:
            collected += sym
            print(sym, end="", flush=True)

    in_stream.stop_stream()
    in_stream.close()
    pa.terminate()

    print(f"\n\n[*] 수집된 HEX: {collected}")
    try:
        if len(collected) % 2 != 0:
            collected = collected[:-1]
        decoded = bytes.fromhex(collected).decode("utf-8", errors="replace")
        print(f"★ 복원된 텍스트: {decoded} ★\n")
    except Exception as err:
        print(f"[!] 디코딩 오류: {err}\n")


def run_messenger():
    print("=" * 50)
    print(f" MFSK 주파수 범위: {BASE_FREQ}Hz ~ {MFSK_FREQ_MAP['STOP']}Hz")
    print(
        f" 심볼 길이: {int(TIME_PER_UNIT * 1000)}ms"
        f" / 가드: {int(GAP_TIME * 1000)}ms"
        f" / HOP: {int(HOP / SAMPLE_RATE * 1000)}ms"
    )
    print("=" * 50)

    while True:
        print("-" * 50)
        print(" 1. MFSK 오디오 전송 (Tx)")
        print(" 2. MFSK 오디오 수신 (Rx)")
        print(" 3. 프로그램 종료")
        print("-" * 50)
        choice = input("메뉴 번호: ").strip().lower()

        if choice == "1":
            transmit_mfsk_signal()
        elif choice == "2":
            capture_and_decode_mfsk()
        elif choice in ("3", "q"):
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    run_messenger()
