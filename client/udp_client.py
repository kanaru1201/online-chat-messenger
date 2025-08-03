import socket

class UDP_Chat_Client:
    def __init__(self, host='localhost', port=9091):
        self.host = host
        self.port = port

    def join_room_only(self, room_name, username, token, is_creator=False):
        if is_creator:
            print(f"作成したルーム '{room_name}' への入室を試行中...")
        else:
            print(f"ルーム '{room_name}' への参加を試行中...")
        
        udp_sock = None
        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_addr = (self.host, self.port)

            join_packet = f"{room_name}|{token}|{username}|__JOIN__"
            print(f"接続パケット送信: {join_packet}")
            udp_sock.sendto(join_packet.encode('utf-8'), server_addr)
            
            if is_creator:
                print(f"作成者として入室リクエストを送信しました...")
            else:
                print(f"参加リクエストを送信しました...")

            try:
                udp_sock.settimeout(3.0)
                print(f"サーバー応答待機中... (タイムアウト: 3秒)")
                
                data, server_response_addr = udp_sock.recvfrom(4096)
                response = data.decode('utf-8')
                print(f"サーバー応答受信: '{response}' from {server_response_addr}")
                
                if "参加が完了しました" in response:
                    if is_creator:
                        print(f"ルーム作成者として入室成功: {response}")
                        print(f"{username} さん、ルーム '{room_name}' の作成と入室が完了しました")
                    else:
                        print(f"ルーム参加成功: {response}")
                        print(f"{username} さん、ルーム '{room_name}' への参加が完了しました")
                    return True
                else:
                    if is_creator:
                        print(f"ルーム作成者入室失敗: {response}")
                    else:
                        print(f"ルーム参加失敗: {response}")
                        if "存在しません" in response or "見つかりません" in response:
                            print(f"ルーム '{room_name}' が存在しません。先にルームを作成してください")
                    return False
                    
            except socket.timeout:
                print("サーバーからの応答がタイムアウトしました（3秒）")
                if is_creator:
                    print("ルーム作成者の入室確認ができませんでした")
                else:
                    print("ルーム参加の確認ができませんでした")
                return False
            except Exception as recv_error:
                print(f"応答受信エラー: {recv_error}")
                return False

        except Exception as e:
            print(f"UDP処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if udp_sock:
                udp_sock.close()
                print("UDPソケットを閉じました")

    def create_and_enter_room(self, room_name, username, token):
        return self.join_room_only(room_name, username, token, is_creator=True)

    def join_existing_room(self, room_name, username, token):
        return self.join_room_only(room_name, username, token, is_creator=False)