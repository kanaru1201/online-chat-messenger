import threading
import time
from server.room_manager import RoomManager
from server.tcp_server import TCPServer
from server.udp_chat_server import UDPChatServer

def run_tcp_server(room_manager):
    tcp_server = TCPServer("localhost", 9090,room_manager)
    try:
        tcp_server.start()
    except KeyboardInterrupt:
        print("[TCP] Ctrl+Cで停止")
        tcp_server.stop(room_manager)

def run_udp_server(room_manager):
    udp_server = UDPChatServer("localhost", 9001,room_manager)
    try:
        udp_server.start()
    except KeyboardInterrupt:
        print("[UDP] Ctrl+Cで停止")

def main():
    room_manager = RoomManager()

    tcp_thread = threading.Thread(target=run_tcp_server, args=(room_manager,), daemon=True)
    udp_thread = threading.Thread(target=run_udp_server, args=(room_manager,), daemon=True)

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