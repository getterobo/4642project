from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

import json
from ryu.app import simple_switch_13
from ryu.lib.packet import ether_types
from webob import Response
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
import threading
import os
import tkinter as tk

simple_switch_instance_name = 'simple_switch_api_app'
url = '/simpleswitch/mactable/{dpid}'
ord_list_url = '/simpleswitch/ord_list'
hi_list_url = '/simpleswitch/high_list/{dpid}'
data_usage_url = '/simpleswitch/data_usage/{dpid}'
ban_list_url = '/simpleswitch/ban_list/{dpid}'

print("starting control")
os.system('gnome-terminal -- bash -c "python3 t.py; exec bash"')


class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name: self})
        # threading.Thread(target=self.command_window, daemon=True).start()
        # self.command_window()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})

    def set_mac_to_port(self, dpid, entry):
        mac_table = self.mac_to_port.setdefault(dpid, {})
        datapath = self.switches.get(dpid)

        entry_port = entry['port']
        entry_mac = entry['mac']

        if datapath is not None:
            parser = datapath.ofproto_parser
            if entry_port not in mac_table.values():

                for mac, port in mac_table.items():
                    # from known device to new device
                    actions = [parser.OFPActionOutput(entry_port)]
                    match = parser.OFPMatch(in_port=port, eth_dst=entry_mac)
                    self.add_flow(datapath, 1, match, actions)

                    # from new device to known device
                    actions = [parser.OFPActionOutput(port)]
                    match = parser.OFPMatch(in_port=entry_port, eth_dst=mac)
                    self.add_flow(datapath, 1, match, actions)

                mac_table.update({entry_mac: entry_port})
        return mac_table

    def add_high_lvl_list(self, dpid, entry):
        datapath = self.switches.get(dpid)
        parser = datapath.ofproto_parser
        addr = entry['addr']
        dpid = str(dpid).zfill(16)
        TO = 30
        if len(addr) < 16:
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst='10.0.0.254',
                                    ipv4_src=addr)
            actions = [parser.OFPActionOutput(2)]
            self.logger.info(f"Adding flow: match={match}, actions={actions}")
            self.add_flow(datapath, 20, match, actions)

            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=addr,
                                    ipv4_src='10.0.0.254')
            out_port = self.IP_to_port[dpid][addr]
            actions = [parser.OFPActionOutput(out_port)]
            self.logger.info(f"Adding flow: match={match}, actions={actions}")
            self.add_flow(datapath, 20, match, actions)
            self.add_to_high(dpid, addr, TO, datapath)
            return self.high_list

    def add_to_high(self, dpid, element, timeout, datapath):
        if element not in self.high_list[dpid]:
            print("adding to high")
            self.high_list[dpid].append(element)
            timer = threading.Timer(timeout, self.remove_from_high, args=[dpid, datapath, element])
            timer.start()

    def remove_from_high(self, dpid, datapath, element):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst='10.0.0.254',
                                ipv4_src=element)
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            priority=20,
            match=match)
        datapath.send_msg(flow_mod)

        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src='10.0.0.254',
                                ipv4_dst=element)
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            priority=20,
            match=match)
        datapath.send_msg(flow_mod)

        if element in self.high_list[dpid]:
            self.high_list[dpid].remove(element)

    def lift_ban(self, dpid, entry):
        datapath = self.switches.get(dpid)
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        addr = entry['addr']
        dpid = str(dpid).zfill(16)

        if addr in self.ban_list:
            self.ban_list.remove(addr)
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                    ipv4_src=addr)
            flow_mod = parser.OFPFlowMod(
                datapath=datapath,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                match=match,
                priority=10)
            datapath.send_msg(flow_mod)

            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                    ipv4_dst=addr)
            flow_mod = parser.OFPFlowMod(
                datapath=datapath,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                match=match,
                priority=10)
            datapath.send_msg(flow_mod)

            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                    ipv4_dst=addr)
            out_port = self.IP_to_port[dpid][addr]
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)

            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                    ipv4_src=addr,
                                    ipv4_dst='10.0.0.253')
            out_port = self.IP_to_port[dpid][addr]
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)
        return self.ban_list


class SimpleSwitchController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(SimpleSwitchController, self).__init__(req, link, data, **config)
        self.simple_switch_app = data[simple_switch_instance_name]

    @route('simpleswitch', ord_list_url, methods=['GET'])
    def get_ord_list(self, req, **kwargs):
        simple_switch = self.simple_switch_app
        lst = simple_switch.ord_list

        body = json.dumps(lst)
        return Response(content_type='application/json; charset=UTF-8', body=body)

    @route('simpleswitch', hi_list_url, methods=['GET'])
    def get_high_list(self, req, **kwargs):
        simple_switch = self.simple_switch_app
        lst = simple_switch.high_list

        body = json.dumps(lst)
        return Response(content_type='application/json; charset=UTF-8', body=body)

    @route('simpleswitch', hi_list_url, methods=['POST'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def post_high_lvl(self, req, **kwargs):
        simple_switch = self.simple_switch_app
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        try:
            new_entry = req.json if req.body else {}
        except ValueError:
            raise Response(status=400)

        # if dpid not in simple_switch.IP_to_port:
        #     print("not in list")
        #     return Response(status=404)

        try:
            no_ban = simple_switch.lift_ban(dpid, new_entry)
            high_lvl_list = simple_switch.add_high_lvl_list(dpid, new_entry)
            body = json.dumps(high_lvl_list)
            return Response(content_type='application/json; charset=UTF-8', body=body)
        except Exception as e:
            return Response(status=500, content_type='application/json; charset=UTF-8',
                            body=json.dumps({'error': str(e)}))

    @route('simpleswitch', data_usage_url, methods=['GET'])
    def get_data_usage(self, req, **kwargs):
        simple_switch = self.simple_switch_app
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])

        try:
            new_entry = req.json if req.body else {}

        except ValueError:
            raise Response(status=400)
        dpid = str(dpid).zfill(16)
        usage_list = simple_switch.data_usage[dpid]

        body = json.dumps(usage_list)
        return Response(content_type='application/json; charset=UTF-8', body=body)

    @route('simpleswitch', ban_list_url, methods=['GET'])
    def get_ban(self, req, **kwargs):
        simple_switch = self.simple_switch_app
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])

        try:
            new_entry = req.json if req.body else {}

        except ValueError:
            raise Response(status=400)
        dpid = str(dpid).zfill(16)
        list_of_ban = simple_switch.ban_list

        body = json.dumps(list_of_ban)
        return Response(content_type='application/json; charset=UTF-8', body=body)

    @route('simpleswitch', ban_list_url, methods=['DELETE'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def delete_ban(self, req, **kwargs):
        simple_switch = self.simple_switch_app
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        try:
            new_entry = req.json if req.body else {}
        except ValueError:
            raise Response(status=400)

        try:
            list_of_ban = simple_switch.lift_ban(dpid, new_entry)
            body = json.dumps(list_of_ban)
            return Response(content_type='application/json; charset=UTF-8', body=body)
        except Exception as e:
            return Response(status=500, content_type='application/json; charset=UTF-8',
                            body=json.dumps({'error': str(e)}))