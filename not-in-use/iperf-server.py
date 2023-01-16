import iperf3

def start_server(serverIP, port, verbose=True):

    print(f'Starting Iperf3 server on {serverIP}:{port}...')

    server = iperf3.Server()
    server.bind_address = serverIP
    server.port = port
    server.verbose = verbose

    while True:
        server.run()

    pass

start_server('10.0.0.1', 6969)
