from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
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

    POLLING_INTERVAL = 10
    MAX_THR = 1e9/8


    def __init__(self, *args, **kwargs):
        super(CustomSwitch, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.net = nx.DiGraph()
        self.interfaces = {}
        self.topology_api_app = self
        self.routing = {}

    # nasz "MAIN"
    def _monitor(self):

        while True:

            time.sleep(CustomSwitch.POLLING_INTERVAL)
            print()
            print(4*'*', 'NEXT INTERVAL', 4*'*')
            print()

            for dp in self.datapaths.values():
                self._request_stats(dp)

            # for link in self.net.edges(data=True):
            #     print(link)
                
            self.routing = self.dijkstra()
            print(f'New routing: {self.routing}')

            #print(f'Self.datapaths: {self.datapaths}')

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

        for link in self.net.edges(data=True):
            print(link)
        for switch in switch_list:
          print(switch)

        # interfaces[source, port] = destination
        for v,w,data in self.net.edges(data=True):
            self.interfaces[v,data['port']] = w

        print(f'Udalo sie wykryc i zapisac topologie:')
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

            print(f'Dodoano flow: DATAPATH ID: {dp.id}, IP DST {ip_dst}')


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

        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):

        body = ev.msg.body

        print(f'Wypisywanie statystyk dla FLOW (...)')

        # self.logger.info('datapath         '
        #                  'in-port  eth-dst           '
        #                  'out-port packets  bytes')
        # self.logger.info('---------------- '
        #                  '-------- ----------------- '
        #                  '-------- -------- --------')
        # for stat in sorted([flow for flow in body if flow.priority == 1],
        #                    key=lambda flow: (flow.match['in_port'],
        #                                      flow.match['eth_dst'])):
        #     self.logger.info('%016x %8x %17s %8x %8d %8d',
        #                      ev.msg.datapath.id,
        #                      stat.match['in_port'], stat.match['eth_dst'],
        #                      stat.instructions[0].actions[0].port,
        #                      stat.packet_count, stat.byte_count)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):

        body = ev.msg.body
        # print(body)
        # print(ev.msg.datapath.id) # switch id

        # for edge in self.net.edges(data=True):

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

                #print(f'Obliczono nowa wage dla lacza {source} - {destination}')
        
        #print(f'Wypisywanie statystyk dla PORT (...)')
                
        # self.logger.info('datapath         port     '
        #                  'rx-pkts  rx-bytes rx-error '
        #                  'tx-pkts  tx-bytes tx-error')
        # self.logger.info('---------------- -------- '
        #                  '-------- -------- -------- '
        #                  '-------- -------- --------')
        # for stat in sorted(body, key=attrgetter('port_no')):
        #     self.logger.info('      %8d   %8x %8d %8d %8d %8d %8d %8d',
        #                      ev.msg.datapath.id, stat.port_no,
        #                      stat.rx_packets, stat.rx_bytes, stat.rx_errors,
        #                      stat.tx_packets, stat.tx_bytes, stat.tx_errors)    

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

        # struktura przechowujaca ip_hosta - jego gateway ??
        
        #print(f'Datapath: {datapath}')

        #ofproto = dp_value.ofproto
        parser = dp_value.ofproto_parser        

        # wyciagamy ze strunktury routing dla danego datapath [(dp, ip_dst)] : out_port
        for route_key in self.routing.keys():
            if route_key[0] == dp_key:

                ip_dst = route_key[1]
                out_port = self.routing[route_key]

                ip_dst = '10.0.0.' + str(route_key[1])

                #jesli zmaczuje sie nam ip destynacji
                match = parser.OFPMatch(ipv4_dst=ip_dst, eth_type=0x800)

                #to wyslij przez port X
                actions = [parser.OFPActionOutput(port=out_port)]
                
                #wyslij requesta o dodanie takiego flow
                self.add_flow(dp_value, 10, match, actions)

                #print(f'Added flow: switch {dp_key}, route key: {route_key}, ip_dst: {ip_dst}')


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
        #print(f'Msg to add new flow: {mod}')


    # Obsuga arpa

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Create the match criteria for ARP packets
        match = parser.OFPMatch(eth_type=0x0806)

        # Set the action for the flow
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]

        # Create the flow mod message and send it to the switch
        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=0,
                                command=ofproto.OFPFC_ADD, idle_timeout=0,
                                hard_timeout=0, priority=0x8000,
                                flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)



    