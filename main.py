import threading
import time
from server.tcp_server import TCPServer
from server.udp_chat_server import UDPChatServer

def run_tcp_server():
    tcp_server = TCPServer("localhost", 9090)
    try:
        tcp_server.start()
    except KeyboardInterrupt:
        print("[TCP] Ctrl+Cで停止")
        tcp_server.stop()

def run_udp_server():
    udp_server = UDPChatServer("localhost", 9001)
    try:
        udp_server.start()
    except KeyboardInterrupt:
        print("[UDP] Ctrl+Cで停止")

def main():
    tcp_thread = threading.Thread(target=run_tcp_server, daemon=True)
    udp_thread = threading.Thread(target=run_udp_server, daemon=True)

    tcp_thread.start()
    udp_thread.start()

    print("[Main] TCP/UDPサーバー両方起動完了")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Main] Ctrl+C検知。終了します。")

if __name__ == "__main__":
    main()