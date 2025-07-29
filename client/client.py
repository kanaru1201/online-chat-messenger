from tcp_client import TCPClient

def main():
    server_address = input("サーバーアドレス名 (デフォルト: localhost): ").strip() or 'localhost'
    port = input("ポート番号 (デフォルト: 9090): ").strip()
    server_port = int(port) if port else 9090

    try:
        client = TCPClient(server_address, server_port)
        client.connect()
        client.run()
    except KeyboardInterrupt:
        print("\nユーザーが中断しました。")
    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    main()