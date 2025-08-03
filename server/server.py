import threading
import time

from room_manager import RoomManager
from tcp_server import TCP_Create_Join_Server
from udp_server import UDP_Chat_Server

def main():
    room_manager = RoomManager()

    host = input("ホスト名 (デフォルト: localhost): ").strip() or "localhost"

    tcp_port_str = input("TCPポート番号 (デフォルト: 9090): ").strip()
    if tcp_port_str:
        try:
            tcp_port = int(tcp_port_str)
        except ValueError:
            print("ポート番号が不正です。数値で入力してください。")
            return
    else:
        tcp_port = 9090

    udp_port_str = input("UDPポート番号 (デフォルト: 9091): ").strip()
    if udp_port_str:
        try:
            udp_port = int(udp_port_str)
        except ValueError:
            print("ポート番号が不正です。数値で入力してください。")
            return
    else:
        udp_port = 9091

    tcp_server = TCP_Create_Join_Server(host, tcp_port, room_manager)
    udp_server = UDP_Chat_Server(host, udp_port, room_manager)

    tcp_thread = threading.Thread(target=tcp_server.start, daemon=False)
    udp_thread = threading.Thread(target=udp_server.bind, daemon=False)
    
    tcp_thread.start()
    udp_thread.start()

    print(f"サーバー開始完了:")
    print(f"  TCP: {host}:{tcp_port}")
    print(f"  UDP: {host}:{udp_port}")
    print("Ctrl+Cで停止...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+Cで停止")
        tcp_server.stop()
        udp_server.stop()
        tcp_thread.join()
        udp_thread.join()
        print("サーバー停止完了")

if __name__ == "__main__":
    main()