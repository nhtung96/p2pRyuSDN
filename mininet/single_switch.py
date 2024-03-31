from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def create_topology():
    # Create Mininet network
    net = Mininet(controller=None, switch=OVSSwitch)

    # Add remote controller
    controller_ip = '192.168.142.128'
    controller = net.addController('c1', controller=RemoteController, ip=controller_ip)

    # Add Open vSwitch
    switch = net.addSwitch('s1')

    # Add hosts
    hosts = []
    for i in range(3):
        host = net.addHost('h%d' % (i+1))
        hosts.append(host)
        net.addLink(host, switch)

    # Connect switch to controller
    net.addLink(switch, controller)

    # Start Mininet
    net.start()

    # Open Mininet CLI
    CLI(net)

    # Clean up
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()
