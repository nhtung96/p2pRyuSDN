#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def multiControllerNet():
    "Create a network from semi-scratch with multiple controllers."

    net = Mininet(controller=None, switch=OVSSwitch, waitConnected=True)

    info("*** Creating (reference) controllers\n")
    c1_ip = '192.168.142.128'
    c2_ip = '192.168.142.130'
    c3_ip = '192.168.142.131'

    c1 = net.addController('c1', controller=RemoteController, ip=c1_ip)
    c2 = net.addController('c2', controller=RemoteController, ip=c2_ip)
    c3 = net.addController('c3', controller=RemoteController, ip=c3_ip)

    info("*** Creating switches\n")
    s1 = net.addSwitch('s1', dpid="0000000000000001")
    s2 = net.addSwitch('s2', dpid="0000000000000002")
    s3 = net.addSwitch('s3', dpid="0000000000000003")
    s4 = net.addSwitch('s4', dpid="0000000000000004")
    s5 = net.addSwitch('s5', dpid="0000000000000005")
    s6 = net.addSwitch('s6', dpid="0000000000000006")
    s7 = net.addSwitch('s7', dpid="0000000000000007")
    s8 = net.addSwitch('s8', dpid="0000000000000008")
    s9 = net.addSwitch('s9', dpid="0000000000000009")

    info("*** Creating hosts\n")
    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')
    h3 = net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/24')
    h4 = net.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/24')
    h5 = net.addHost('h5', mac='00:00:00:00:00:05', ip='10.0.0.5/24')
    h6 = net.addHost('h6', mac='00:00:00:00:00:06', ip='10.0.0.6/24')
    h7 = net.addHost('h7', mac='00:00:00:00:00:07', ip='10.0.0.7/24')
    h8 = net.addHost('h8', mac='00:00:00:00:00:08', ip='10.0.0.8/24')
    h9 = net.addHost('h9', mac='00:00:00:00:00:09', ip='10.0.0.9/24')  

    info("*** Creating links\n")
    net.addLink(s1, h1)
    net.addLink(s2, h2)
    net.addLink(s3, h3)
    net.addLink(s4, h4)
    net.addLink(s5, h5)
    net.addLink(s6, h6)
    net.addLink(s7, h7)
    net.addLink(s8, h8)
    net.addLink(s9, h9)

    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s3, s1)

    net.addLink(s4, h5)
    net.addLink(s5, s6)
    net.addLink(s6, s4)

    net.addLink(s7, s8)
    net.addLink(s8, s9)
    net.addLink(s9, s7)

    info("*** Starting network\n")
    net.build()
    c1.start()
    c2.start()
    c3.start()
    s1.start([c1])
    s2.start([c1])
    s3.start([c1])
    s4.start([c2])
    s5.start([c2])
    s6.start([c2])
    s7.start([c3])
    s8.start([c3])
    s9.start([c3])

    #info("*** Testing network\n")
    #net.pingAll()

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')  # for CLI output
    multiControllerNet()
