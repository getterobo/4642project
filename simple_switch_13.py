from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib import hub
from ryu.lib.packet import ether_types


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.IP_to_port = {}
        self.ord_list = {}
        self.high_list = {}
        self.data_usage = {}

        self.ban_list = []
        self.dp = []
        self.data = {}
        self.lim = 1000
        self.TO = 20
        self.sleeptime = 20
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.datapaths[datapath.id] = datapath

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        dpid = format(datapath.id, "d").zfill(16)
        self.data.setdefault(dpid, {})
        self.data_usage.setdefault(dpid, {})

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        src_last_2 = src[-2:-1]
        if src_last_2 == "ff": return

        dpid = format(datapath.id, "d").zfill(16)

        self.mac_to_port.setdefault(dpid, {})
        self.IP_to_port.setdefault(dpid, {'10.0.0.253': 1})
        self.ord_list.setdefault(dpid, [])
        self.high_list.setdefault(dpid, [])

        IP4 = pkt.get_protocol(ipv4.ipv4)
        if IP4:
            parts = IP4.src.split('.')
            last = parts[3]
            if last == 254 or last == 253:
                return
            if IP4.src not in self.IP_to_port[dpid]:
                self.IP_to_port[dpid][IP4.src] = in_port
            if IP4.src not in self.ord_list[dpid] and IP4.src != '10.0.0.253' and IP4.src != '10.0.0.254':
                self.ord_list[dpid].append(IP4.src)
            if IP4.src not in self.data_usage[dpid] and IP4.src != '10.0.0.253' and IP4.src != '10.0.0.254':
                self.data_usage[dpid][IP4.src] = 0
            ip_dst = IP4.dst
            ip_src = IP4.src
            if ip_src != '10.0.0.254':
                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=ip_src)
                actions = [parser.OFPActionOutput(in_port)]
                self.add_flow(datapath, 1, match, actions)
        if self.ord_list[dpid]:
            for x in range(len(self.ord_list[dpid])):
                ip_src = self.ord_list[dpid][x]
                IP_dst = '10.0.0.253'
                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=IP_dst,
                                        ipv4_src=ip_src)
                actions = [parser.OFPActionOutput(1)]
                self.add_flow(datapath, 1, match, actions)

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port
        # self.logger.info(self.IP_to_port)

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                # self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                # self.add_flow(datapath, 1, match, actions)
                return
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        lim = self.lim
        TO = self.TO
        # self.logger.info('datapath         '
        #                  'eth-dst           '
        #                  'out-port packets  bytes')
        # self.logger.info('---------------- '
        #                  '----------------- '
        #                  '-------- -------- --------')
        self.logger.info("==========================")
        self.logger.info("checking data usage")
        print(self.data_usage)
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['ipv4_dst'])):
            # self.logger.info('%016x %17s %8x %8d %8d',
            #                  ev.msg.datapath.id,
            #                  stat.match['ipv4_dst'],
            #                  stat.instructions[0].actions[0].port,
            #                  stat.packet_count, stat.byte_count)
            # self.data[ev.msg.datapath.id][stat.match['ipv4_dst']] = stat.byte_count
            dpid = format(ev.msg.datapath.id, "d").zfill(16)
            h_id = stat.match['ipv4_dst']
            if h_id == '10.0.0.253' or h_id == '10.0.0.254':
                continue
            self.data[dpid][h_id] = stat.byte_count
            data_prev = self.data_usage[dpid][h_id]
            data_now = stat.byte_count
            data_used = data_now - data_prev
            self.logger.info("-----------")
            self.logger.info("User: %s, used: %s", h_id, data_used)
            if (h_id not in self.high_list[dpid]) and (
                    h_id in self.data_usage[dpid]) and h_id != '10.0.0.253' and h_id != '10.0.0.254':
                if data_used >= lim:
                    self.ban_list.append(h_id)
                    datapath = ev.msg.datapath
                    ofproto = datapath.ofproto
                    parser = datapath.ofproto_parser
                    match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                            ipv4_src=h_id)
                    actions = []
                    self.add_flow(datapath, 10, match, actions,
                                  idle_timeout=TO,
                                  hard_timeout=TO)
                    match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                            ipv4_dst=h_id)
                    actions = []
                    self.add_flow(datapath, 10, match, actions,
                                  idle_timeout=TO,
                                  hard_timeout=TO)
                    self.logger.info("------------------")
                    self.logger.info("User: %s, is banned for %s", h_id, TO)
                else:
                    if h_id in self.ban_list:
                        self.ban_list.remove(h_id)
            self.data_usage[dpid][h_id] = data_now

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(self.sleeptime)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)