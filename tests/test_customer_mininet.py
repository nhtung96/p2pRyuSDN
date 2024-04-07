from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.topo import SingleSwitchTopo
from mininet.cli import CLI
from mininet.log import setLogLevel

def create_topology():
    # Create Mininet network
    net = Mininet(controller=None, switch=OVSSwitch, ipBase='10.1.1.0/24')

    # Add remote controllers
    controllers = []
    controller_ips = ['192.168.142.128', '192.168.142.130', '192.168.142.131']
    controller_ports = [6653, 6654, 6655]
    for ip, port in zip(controller_ips, controller_ports):
        controllers.append(net.addController('c%d' % (port-6652), controller=RemoteController, ip=ip, port=port))

    # Add Open vSwitch with OpenFlow 1.3 support
    switch = net.addSwitch('s1', protocols='OpenFlow13')

    # Add hosts
    num_hosts = 4
    for i in range(num_hosts):
        host = net.addHost('h%d' % (i+1))

    # Connect hosts to switch
    for i in range(num_hosts):
        net.addLink('h%d' % (i+1), switch)

    # Start Mininet
    net.build()
    for controller in controllers:
        controller.start()
    switch.start(controllers)

    # Open Mininet CLI
    CLI(net)

    # Clean up
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()
