# TCPサーバ・UDPサーバで共有するルーム名とトークンの格納用配列
rooms = {}   # {room_name: {'host': username, 'members': [usernames]}}
tokens = {}  # {token: (room_name, username, is_host)}