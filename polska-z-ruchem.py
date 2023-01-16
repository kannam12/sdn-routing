#command: sudo python3 polska-z-ruchem.py

from mininet.topo import Topo
import networkx as nx
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import argparse
from random import sample
# from mininet.node import Controller
from mininet.node import OVSController
from mininet.node import RemoteController


class MyTopoFromGML( Topo ):  

    def build( self ):
        "Load topo form .gml file."

        GRAPH = nx.read_gml('topo-polska.gml')  #works also for other .gml files, eg. janos

        node_names = list(GRAPH.nodes)  #helper for list()
        numbers = [i for i in range (len(node_names))]  #helper for dictionary creating

        NODES = dict(zip(node_names, numbers))

        for i in range (len(GRAPH.nodes)):
            self.addSwitch(f's_{i}')    #has to be number, not city name
            self.addHost(f'h_{ node_names[i] }')        
            self.addLink(f'h_{ node_names[i] }', f's_{i}')

        for(n1, n2) in GRAPH.edges:
            self.addLink(f's_{ NODES[n1] }', f's_{ NODES[n2] }')


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

        node_count = len(cities)

        sw = [ f's{i}' for i in range (node_count)]     #s1, s2....

        Hosts = [ self.addHost(str(city)) for city in cities ]       
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

topos = {   'from-gml': ( lambda: MyTopoFromGML() ),
            'fixed':    ( lambda: PolskaTopoFixed() ) } 

def run():
    setLogLevel('info')	
    
    topo = None

    if args.topo == 'fixed':
        topo = PolskaTopoFixed()
    elif args.topo == 'from-gml':
        topo = MyTopoFromGML()
    else:
        topo = PolskaTopoFixed()


    #net = Mininet(topo=topo)
    net = Mininet(topo = topo)
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=5555)

    net.start()

    # for switch in net.switches:
    #     switch.start([controller])
    i = 0
    for h in net.hosts:
        ips = ''
        for h_temp in net.hosts:
             if h != h_temp:
                ips += h_temp.IP() + ' '
      #  h.cmdPrint( f'./generate_traffic.sh "{ips}" "{h.IP()}" &')
        i += 1

    CLI(net)
    net.stop()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--topo')
    args = parser.parse_args()
    # Tell mininet to print useful information		
    setLogLevel('info')		
    run()   