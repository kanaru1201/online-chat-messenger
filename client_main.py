from client.tcp_client import TCPClient
from client.udp_chat_client import UDPChatClient

def main():
    server_ip = "127.0.0.1"
    tcp_port = 9090
    udp_port = 0  # OSに任せる
    operation = input("操作（1: 作成, 2: 参加）: ").strip()
    op_code = 1 if operation == "1" else 2

    room_name = input("ルーム名: ").strip()
    username = input("ユーザー名: ").strip()

    tcp_client = TCPClient(server_ip, tcp_port)
    tcp_client.connect()

    try:
        token = tcp_client.get_token(room_name, username, op_code)
    except Exception as e:
        print(f"[エラー] トークン取得失敗: {e}")
        return

    print(f"[TCP] トークン取得成功: {token}")

    client = UDPChatClient(
        username=username,
        server_ip=server_ip,
        room_name=room_name,
        token=token,
        local_port=udp_port
    )
    client.start()

if __name__ == "__main__":
    main()