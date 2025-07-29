import threading
from tcp_server import TCPServer

def main():
    host = input("ホスト名 (デフォルト: localhost): ").strip() or "localhost"

    port_str = input("ポート番号 (デフォルト: 9090): ").strip()
    if port_str:
        try:
            port = int(port_str)
        except ValueError:
            print("ポート番号が不正です。数値で入力してください。")
            return
    else:
        port = 9090

    server = TCPServer(host, port)

    thread = threading.Thread(target=server.start, daemon=False)
    thread.start()

    try:
        thread.join()
    except KeyboardInterrupt:
        print("\nCtrl+Cで停止")
        server.stop()
        thread.join()
        print("サーバー停止完了")

if __name__ == "__main__":
    main()