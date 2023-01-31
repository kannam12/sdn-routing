#command: sudo python3 polska-z-ruchem.py

from mininet.topo import Topo
import networkx as nx
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import argparse
from random import sample
from mininet.link import TCLink

from mininet.node import RemoteController


class MyTopoFromGML( Topo ):  

    def build( self ):
        "Load topo form .gml file."

        GRAPH = nx.read_gml('topos/topo-polska.gml')  #works also for other .gml files, eg. janos

        node_names = list(GRAPH.nodes)  #helper for list()
        numbers = [i+1 for i in range (len(node_names))]  #helper for dictionary creating

        NODES = dict(zip(node_names, numbers))

        node_names.sort()

        for i in range (len(GRAPH.nodes)):
            self.addSwitch(f's{i+1}')    #has to be number, not city name
            self.addHost(f'{ node_names[i] }')        
            self.addLink(f'{ node_names[i] }', f's{i+1}')

        for(n1, n2) in GRAPH.edges:
            self.addLink(f's{ NODES[n1] }', f's{ NODES[n2] }')

class PolskaTopoNoLoops( Topo ):  

    def build( self ):
        "Create custom topo."

        cities = [  'Szczecin',
                    'Kolobrzeg',
                    'Gdansk',
                    'Bialystok',
                    'Rzeszow',
                    'Krakow',
                    'Katowice',
                    'Wroclaw',
                    'Poznan',
                    'Bydgoszcz',
                    'Warszawa',
                    'Lodz'] 

        cities.sort()
        node_count = len(cities)

        sw = [ f's{i+1}' for i in range (node_count)]     #s1, s2....

        macs = {}
        i = 1
        for city in cities:
            mac_end = str(i) if i >=10 else '0'+str(i)
            macs[city] = "00:00:00:00:00:" + mac_end
            i += 1

        ips = {}
        i = 1
        for city in cities:
            ips[city] = "10.0.0." + str(i)
            i += 1

        Hosts = [ self.addHost(str(city), mac=macs[city], ip=ips[city]) for city in cities ]    
        Switches = [ self.addSwitch(str(s)) for s in sw ] 

        # Add links
        for i in range (node_count):
            self.addLink( Hosts[i] , Switches[i] )

        for i in range (node_count-1):
            self.addLink( Switches[i], Switches[i+1] )

        # temporarily remove loops
            
        # self.addLink( Switches[0], Switches[8] )
        # self.addLink( Switches[1], Switches[9] )
        # self.addLink( Switches[2], Switches[10] )
        # self.addLink( Switches[3], Switches[10] )
        # self.addLink( Switches[5], Switches[10] )
        # self.addLink( Switches[6], Switches[11] )
        # self.addLink( Switches[7], Switches[11] )
        # self.addLink( Switches[10], Switches[11] )


class PolskaTopoFixed( Topo ):  

    def build( self ):
        "Create custom topo."

        cities = [  'Szczecin',
                    'Kolobrzeg',
                    'Gdansk',
                    'Bialystok',
                    'Rzeszow',
                    'Krakow',
                    'Katowice',
                    'Wroclaw',
                    'Poznan',
                    'Bydgoszcz',
                    'Warszawa',
                    'Lodz'] 

        cities.sort()

        node_count = len(cities)

        sw = [ f's{i+1}' for i in range (node_count)]     #s1, s2....

        macs = {}
        i = 1
        for city in cities:
            mac_end = str(i) if i >=10 else '0'+str(i)
            macs[city] = "00:00:00:00:00:" + mac_end
            i += 1

        ips = {}
        i = 1
        for city in cities:
            ips[city] = "10.0.0." + str(i)
            i += 1

        Hosts = [ self.addHost(str(city), mac=macs[city], ip=ips[city]) for city in cities ]           
        Switches = [ self.addSwitch(str(s)) for s in sw ] 

        # Add links
        for i in range (node_count):
            self.addLink( Hosts[i] , Switches[i], cls=TCLink, bw=1)

        for i in range (node_count-1):
            self.addLink( Switches[i], Switches[i+1], cls=TCLink, bw=1)
            
        self.addLink( Switches[0], Switches[8], cls=TCLink, bw=1)
        self.addLink( Switches[1], Switches[9], cls=TCLink, bw=1)
        self.addLink( Switches[2], Switches[10], cls=TCLink, bw=1)
        self.addLink( Switches[3], Switches[10], cls=TCLink, bw=1)
        self.addLink( Switches[5], Switches[10], cls=TCLink, bw=1)
        self.addLink( Switches[6], Switches[11], cls=TCLink, bw=1)
        self.addLink( Switches[7], Switches[11], cls=TCLink, bw=1)
        self.addLink( Switches[10], Switches[11], cls=TCLink, bw=1)

topos = {   'from-gml':         ( lambda: MyTopoFromGML() ),
            'fixed':            ( lambda: PolskaTopoFixed() ),
            'fixed-no-loops':   ( lambda: PolskaTopoNoLoops() ) } 

def run():
    setLogLevel('info')	
    
    topo = None

    if args.topo == 'fixed-no-loops':
        topo = PolskaTopoNoLoops()    
    elif args.topo == 'fixed':
        topo = PolskaTopoFixed()
    elif args.topo == 'from-gml':
        topo = MyTopoFromGML()
    else:
        topo = PolskaTopoFixed()


    #net = Mininet(topo=topo)
    myController = RemoteController( 'c0', ip='127.0.0.1', port=5555 )
    net = Mininet(topo, controller=myController)

    net.start()

    # for switch in net.switches:
    #     switch.start([controller])
    for h in net.hosts:
        ips = ''
        for h_temp in net.hosts:
             if h != h_temp and h_temp.IP() != '10.0.0.6' and h_temp.IP() != '10.0.0.3':
                ips += h_temp.IP() + ' '
        h.cmdPrint( f'./generate_traffic.sh "{ips}" "{h.IP()}" &')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--topo')
    args = parser.parse_args()
    # Tell mininet to print useful information		
    setLogLevel('info')		
    run()   