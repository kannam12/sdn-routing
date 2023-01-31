from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.lib.packet import packet, ipv4, ethernet, ether_types

import networkx as nx
import time
import pprint


class CustomSwitch(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    POLLING_INTERVAL = 20
    MAX_THR = 1e9/8

    cities = {1:'Szczecin',
    2:'Kolobrzeg',
    3:'Gdansk',
    4:'Bialystok',
    5:'Rzeszow',
    6:'Krakow',
    7:'Katowice',
    8:'Wroclaw',
    9:'Poznan',
    10:'Bydgoszcz',
    11:'Warszawa',
    12:'Lodz'}

    prev_counters=[{}]+[{} for city in cities]

    def __init__(self, *args, **kwargs):
        super(CustomSwitch, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.net = nx.DiGraph()
        self.interfaces = {}
        self.topology_api_app = self
        self.routing = {}
        self.mac_to_port = {}


    # nasz "MAIN"
    def _monitor(self):

        while True:

            time.sleep(CustomSwitch.POLLING_INTERVAL)
            print()
            print(4*'*', 'NEXT INTERVAL', 4*'*')
            print()

            for dp in self.datapaths.values():
                self._request_stats(dp)
                
            self.routing = self.dijkstra()

            for dp_key in self.datapaths:
                dp_value = self.datapaths[dp_key]
                self.update_flowtable(dp_key, dp_value)


    # source: https://sdn-lab.com/2014/12/25/shortest-path-forwarding-with-openflow-on-ryu/ 
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        switch_list = get_switch(self.topology_api_app, None)
        switches = [switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        links = [(link.src.dpid,link.dst.dpid,{'port':link.src.port_no, 'waga': 1, 'bytesTx': 0}) for link in links_list]
        self.net.add_nodes_from(switches)
        self.net.add_edges_from(links)

        for v,w,data in self.net.edges(data=True):
            self.interfaces[v,data['port']] = w

        print(f'Udalo sie wykryc i zapisac topologie w postaci:')
        print(self.net.nodes(data=True))
        print(self.net.edges(data=True))


    # Dodanie flow kierujcego s1 -> h1
    @set_ev_cls(event.EventSwitchEnter)
    def add_host_switch_flows(self, ev):

        for dp in self.datapaths.values():

            parser = dp.ofproto_parser   

            ip_dst = '10.0.0.' + str(dp.id)

            match = parser.OFPMatch(ipv4_dst=ip_dst, eth_type=0x800)
            actions = [parser.OFPActionOutput(port=1)]
            self.add_flow(dp, 5, match, actions, hard_timeout=0)

    
    # Obsuga arp request na flood oraz arp reply s -> h
    @set_ev_cls(event.EventSwitchEnter)
    def add_arp_flows(self, ev):

        for dp in self.datapaths.values():

            parser = dp.ofproto_parser
            ofproto = dp.ofproto   

            ip_dst = '10.0.0.' + str(dp.id)


            ## JEST TAKI FRAGMENT W SIMPLE SWITCH 13, opisany https://osrg.github.io/ryu-book/en/html/switching_hub.html
            
            # # learn a mac address to avoid FLOOD next time.
            # self.mac_to_port[dp.id][src] = in_port

            # # if the destination mac address is already learned,
            # # decide which port to output the packet, otherwise FLOOD
            # if dst in self.mac_to_port[dpid]:
            #     out_port = ...
            # else:


            flood_or_port = ofproto.OFPP_FLOOD # <- o z tym pewnie trzeba cos zrobic
            # a jakby sprobowac arpa puscic raz tym naszym routingiem? i wtedy olac flow na flood?

            match = parser.OFPMatch(eth_type=0x0806)
            actions = [parser.OFPActionOutput(flood_or_port)]
            self.add_flow(dp, 2, match, actions, hard_timeout=0)

            match = parser.OFPMatch(arp_tpa=ip_dst, eth_type=0x0806)
            actions = [parser.OFPActionOutput(port=1)]
            self.add_flow(dp, 2, match, actions, hard_timeout=0)


    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):

        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):

        body = ev.msg.body

        print(f'Wypisywanie statystyk dla {ev.msg.datapath.id}:{self.cities[ev.msg.datapath.id]}')
        self.logger.info('datapath         '
                         'eth_type  ipv4_dst         '
                         'out-port packets  bytes  speed')
        # for stat in [flow for flow in body if flow.priority == 10]:
        #     print(stat)
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 10],
                           key=lambda flow: (flow.match['eth_type'],
                                             flow.match['ipv4_dst'])):
            if stat.match['ipv4_dst'] not in self.prev_counters[ev.msg.datapath.id].keys():
                self.prev_counters[ev.msg.datapath.id][stat.match['ipv4_dst']]=0
            self.logger.info('%016x %8x %17s %8x %8d %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['eth_type'], stat.match['ipv4_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count,
                             (stat.byte_count-self.prev_counters[ev.msg.datapath.id][stat.match['ipv4_dst']])/(self.POLLING_INTERVAL))
            self.prev_counters[ev.msg.datapath.id][stat.match['ipv4_dst']]=stat.byte_count

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):

        body = ev.msg.body

        for stat in sorted(body, key=attrgetter('port_no')):

            if (ev.msg.datapath.id, stat.port_no) in self.interfaces.keys():
                current = stat.tx_bytes
                source = ev.msg.datapath.id
                destination = self.interfaces[ev.msg.datapath.id, stat.port_no]
                current_thr = (self.net[source][destination]['bytesTx'] - current)/CustomSwitch.POLLING_INTERVAL
                percent = current_thr/CustomSwitch.MAX_THR*100
                nowa_waga = percent*percent
                        
                self.net[source][destination]['waga'] = nowa_waga
                self.net[source][destination]['bytesTx'] = current


    def dijkstra(self):

        routing = {}

        try:
            for source in self.net.edges(data=True):
                for destination in self.net.edges(data=True):
                    if (destination != source):
                        path = nx.dijkstra_path(self.net, source[0], destination[0], weight='waga')
                        #print(path)
                        if(len(path)>1):
                            if(source[0] == path[0] and source[1] == path[1]):
                                #print(source)
                                interface = source[2]['port']
                                routing[(source[0], destination[0])] = interface
        except nx.NetworkXNoPath:
            print('No path')

        return routing

    # source: ryu/app/simple_switch_13.py
    def update_flowtable(self, dp_key, dp_value):

        parser = dp_value.ofproto_parser        

        # wyciagamy ze strunktury routing dla danego datapath [(dp, ip_dst)] : out_port
        for route_key in self.routing.keys():
            if route_key[0] == dp_key:

                ip_dst = route_key[1]
                out_port = self.routing[route_key]

                ip_dst = '10.0.0.' + str(route_key[1])

                #jesli zmaczuje sie nam ip destynacji to wyslij na port X
                match = parser.OFPMatch(ipv4_dst=ip_dst, eth_type=0x800)
                actions = [parser.OFPActionOutput(port=out_port)]
                self.add_flow(dp_value, 10, match, actions)

                match = parser.OFPMatch(arp_tpa=ip_dst, eth_type=0x806) # mozna jeszcze pokminic z arp_op ktore mowi czy arp request czy replay
                actions = [parser.OFPActionOutput(port=out_port)]
                self.add_flow(dp_value, 2, match, actions)


    def add_flow(self, datapath, priority, match, actions, buffer_id=None, hard_timeout=21):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, hard_timeout=hard_timeout)
        datapath.send_msg(mod)
