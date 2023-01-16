import iperf3

def start_client(clientIP, serverIP, port, duration=3, protocol='tcp', blksize=1234, num_streams=10, verbose=True):

    print(f'Starting Iperf3 client as {clientIP} to {serverIP}:{port}...')

    client = iperf3.Client()
    client.duration = duration
    client.bind_address = clientIP
    client.server_hostname = serverIP
    client.port = port
    client.protocol = protocol
    client.blksize = blksize
    client.num_streams = num_streams
    client.zerocopy = True
    client.verbose = verbose
    client.reverse = True

    result = client.run()

    return result

def print_result(result, toFile=False):

    if result.error:
        print(result.error)

    else:
        print('Test completed:')
        print('  started at         {0}'.format(result.time))
        print(' ------ ')

        if toFile:
            f = open('last-result.txt', mode='w')
            f.write(str(result))
            f.close()
            print('Test results written to last-result.txt file')


        #przykadowy kawaek kodu ktory w sumie powinien zadzialac

        #print(result)
        # print('  bytes transmitted  {0}'.format(result.bytes))
        # print('  jitter (ms)        {0}'.format(result.jitter_ms))
        # print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

        # print('Average transmitted data in all sorts of networky formats:')
        # print('  bits per second      (bps)   {0}'.format(result.bps))
        # print('  Kilobits per second  (kbps)  {0}'.format(result.kbps))
        # print('  Megabits per second  (Mbps)  {0}'.format(result.Mbps))
        # print('  KiloBytes per second (kB/s)  {0}'.format(result.kB_s))
        # print('  MegaBytes per second (MB/s)  {0}'.format(result.MB_s))

def random2IP(num_nodes):

    import random

    ip1 = f'10.0.0.{random.randint(1, num_nodes)}'

    while True:
        ip2 = f'10.0.0.{random.randint(1, num_nodes)}'
        if ip1 != ip2:
            break   

    return ip1, ip2

##########

num_nodes = 12      #dla topo polska
clientIP, serverIP = random2IP(num_nodes)
port = 6969

#ToDo: uruchamianie servera w drugim watku/ w tle (?)
serverIP = '10.0.0.1'   #na razie na pale zawsze na tym adresie

result = start_client(clientIP, serverIP, port)
print_result(result, True)






