if __name__ == "__main__":
    from TCPServer import TCPServer  # TCPServerクラスを定義した別ファイルと仮定
    from UDPServer import UDPServer  # UDPServerクラスを定義した別ファイルと仮定
    import threading

    # TCPサーバ起動
    tcp_server = TCPServer(host='localhost', port=9090)
    tcp_thread = threading.Thread(target=tcp_server.start, daemon=True)

    # UDPサーバ起動
    udp_server = UDPServer(host='0.0.0.0', port=9999)
    udp_thread = threading.Thread(target=udp_server.start, daemon=True)

    # スレッド開始
    tcp_thread.start()
    udp_thread.start()

    print("TCPおよびUDPサーバーが起動しました")

    try:
        while True:
            pass  # 無限ループでメインスレッド維持
    except KeyboardInterrupt:
        print("\nサーバーを終了します")