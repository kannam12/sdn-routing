#command: sudo mn --custom polska.py --topo from-gml
#if you don't have a file, try --topo fixed

from mininet.topo import Topo
import networkx as nx

class MyTopoFromGML( Topo ):  

    def __init__( self ):
        "Load topo form .gml file."

        # Initialize topology
        Topo.__init__( self )

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

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

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
            
        # self.addLink( Switches[0], Switches[8] )
        # self.addLink( Switches[1], Switches[9] )
        # self.addLink( Switches[2], Switches[10] )
        # self.addLink( Switches[3], Switches[10] )
        # self.addLink( Switches[5], Switches[10] )
        # self.addLink( Switches[6], Switches[11] )
        # self.addLink( Switches[7], Switches[11] )
        # self.addLink( Switches[10], Switches[11] )

topos = {   'from-gml': ( lambda: MyTopoFromGML() ),
            'fixed':    ( lambda: MyTopoFromGML() ) }  
