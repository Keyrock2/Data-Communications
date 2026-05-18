import random
import socket
import sys
from argparse import ArgumentParser

LOTTO_MIN = 1
LOTTO_MAX = 45
LOTTO_PICK = 6
BUFFER_SIZE = 65536


def parse_user_picks(raw_text):
    """원본 문자열을 정수 리스트로 변환 (쉼표/공백 모두 허용)"""
    cleaned = raw_text.replace(",", " ")
    tokens = cleaned.split()
    if not tokens:
        return []
    return list(map(int, tokens))


def validate_picks(picks):
    """유효성 검사. 문제 있으면 에러 메시지, 정상이면 None 반환"""
    count = len(picks)
    if count > LOTTO_PICK:
        return f"입력 가능한 번호는 최대 {LOTTO_PICK}개입니다. (입력: {count}개)"
    if len(set(picks)) != count:
        return "중복된 번호가 입력되었습니다."
    for n in picks:
        if not (LOTTO_MIN <= n <= LOTTO_MAX):
            return f"번호는 {LOTTO_MIN}~{LOTTO_MAX} 범위여야 합니다. (잘못된 값: {n})"
    return None


def fill_lotto(picks):
    """사용자 선택 번호를 기반으로 6개를 채움. (최종번호, 자동선택분) 반환"""
    chosen = set(picks)
    candidates = set(range(LOTTO_MIN, LOTTO_MAX + 1)) - chosen
    need = LOTTO_PICK - len(chosen)

    pool = list(candidates)
    random.shuffle(pool)
    auto = pool[:need]

    return sorted(chosen | set(auto)), sorted(auto)


def build_response(picks):
    """클라이언트 요청을 받아 응답 문자열 생성"""
    err = validate_picks(picks)
    if err is not None:
        return f"[ERROR] {err}"

    final_nums, auto_nums = fill_lotto(picks)
    user_part = ", ".join(map(str, sorted(picks))) if picks else "(없음)"
    auto_part = ", ".join(map(str, auto_nums)) if auto_nums else "(없음)"
    final_part = " ".join(map(str, final_nums))

    return (
        f"== 로또 번호 추천 ==\n"
        f"수동 선택: {user_part}\n"
        f"자동 선택: {auto_part}\n"
        f"최종 번호: {final_part}"
    )


def serve(host, port):
    """UDP 서버 메인 루프"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.bind((host, port))
        print(f"[로또 서버 가동] {host}:{port} 에서 요청을 대기합니다.")

        while True:
            raw, addr = udp_sock.recvfrom(BUFFER_SIZE)
            try:
                request_text = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                udp_sock.sendto("[ERROR] 디코딩 실패".encode("utf-8"), addr)
                continue

            print(f"  >> {addr} 수신: '{request_text}'")

            try:
                picks = parse_user_picks(request_text)
                reply = build_response(picks)
            except ValueError:
                reply = "[ERROR] 숫자가 아닌 값이 포함되어 있습니다."
            except Exception as ex:
                reply = f"[ERROR] 처리 중 예외 발생: {ex}"

            udp_sock.sendto(reply.encode("utf-8"), addr)
            print(f"  << {addr} 응답 전송 완료")


if __name__ == "__main__":
    ap = ArgumentParser(description="UDP 기반 로또 번호 생성 서버")
    ap.add_argument("--address", type=str, default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3034)
    args, _ = ap.parse_known_args()

    try:
        serve(args.address, args.port)
    except KeyboardInterrupt:
        print("\n[서버 종료]")
        sys.exit(0)
