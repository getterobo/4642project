from mininet.link import TCLink
from mininet.node import RemoteController, OVSSwitch
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
import os


class CustomTopo(Topo):
    def __init__(self, **opts):
        # Initialize topology
        Topo.__init__(self, **opts)

        s1 = self.addSwitch('s1')
        gateway1 = self.addHost('h99', ip='10.0.0.253', mac='00:00:00:00:00:fe')
        gateway2 = self.addHost('h100', ip='10.0.0.254', mac='00:00:00:00:00:ff')
        self.addLink(gateway1, s1, port1=0, port2=1, bw=5)
        self.addLink(gateway2, s1, port1=0, port2=2, bw=200)

        arr_host = []
        for x in range(5):
            arr_host.append(
                self.addHost(f"h{x + 1}", ip=f"10.0.0.{x + 1}", mac=f"00:00:00:00:00:{str(x + 1).zfill(2)}"))

        for x in range(len(arr_host)):
            self.addLink(s1, arr_host[x], bw=200)


def run_custom_topo():
    topo = CustomTopo()
    net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('C0', controller=RemoteController, ip=
    "127.0.0.1", port=6633, protocols="OpenFLow13")
    net.start()
    # for i in range(5):
    #     h = net.get(f'h{i + 1}')
    #     h.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1')
    #     h.cmd('sysctl -w net.ipv6.conf.default.disable_ipv6=1')
    #     h.cmd('sysctl -w net.ipv6.conf.lo.disable_ipv6=1')
    #     h.cmd(f'ip route add default via 10.0.0.254')
    for host in net.hosts:
        host.cmd('ping -c 1 10.0.0.253')
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run_custom_topo()