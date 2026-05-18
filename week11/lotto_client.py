import socket
import sys
from argparse import ArgumentParser

BUFFER_SIZE = 65536
EXIT_KEYWORDS = ("q", "quit", "exit")


def show_help():
    print("-" * 48)
    print(" 1~45 범위의 번호를 0~6개 입력하세요.")
    print(" - 공백 또는 쉼표로 구분")
    print(" - 빈 입력은 완전 자동 추천")
    print(" - 'exit' 또는 'q' 입력 시 종료")
    print("-" * 48)


def request_once(sock, target, line):
    """한 번의 요청-응답 사이클 처리"""
    sock.sendto(line.encode("utf-8"), target)
    print(f"  [전송] '{line}' -> {target}")
    payload, src = sock.recvfrom(BUFFER_SIZE)
    return payload.decode("utf-8"), src


def run_client(target_host, target_port):
    target = (target_host, target_port)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
        print(f"[클라이언트 시작] 대상 서버: {target_host}:{target_port}")

        while True:
            show_help()
            try:
                line = input("번호 입력 >> ").strip()
            except EOFError:
                break

            if line.lower() in EXIT_KEYWORDS:
                print("종료합니다.")
                break

            try:
                answer, src = request_once(client_sock, target, line)
                print(f"  [수신] {src} 로부터:")
                print(answer)
            except socket.error as se:
                print(f"  [소켓 오류] {se}")
            except Exception as ex:
                print(f"  [예외] {ex}")


if __name__ == "__main__":
    ap = ArgumentParser(description="UDP 로또 클라이언트")
    ap.add_argument("--address", type=str, default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3034)
    args, _ = ap.parse_known_args()

    try:
        run_client(args.address, args.port)
    except KeyboardInterrupt:
        print("\n[클라이언트 종료]")
        sys.exit(0)
