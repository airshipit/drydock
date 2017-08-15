# Setup fake IPMI network
ip link add oob-br type bridge
ip link set dev oob-br up

# Setup rack 1 PXE network
ip link add pxe1-br type bridge
ip link set dev pxe1-br up

# Setup rack 2 PXE network
ip link add pxe2-br type bridge
ip link set dev pxe2-br up

# Setup interface to hold all IP addresses for vbmc instances
ip link add dev oob-if type veth peer name oob-ifp
ip link set dev oob-ifp up master oob-br
ip link set dev oob-if up arp on

# Setup rack 1 PXE gateway
ip link add dev pxe1-if type veth peer name pxe1-ifp
ip link set dev pxe1-ifp up master pxe1-br
ip link set dev pxe1-if up arp on
ip addr add 172.24.1.1/24 dev pxe1-if

# Setup rack 2 PXE gateway
ip link add dev pxe2-if type veth peer name pxe2-ifp
ip link set dev pxe2-ifp up master pxe2-br
ip link set dev pxe2-if up arp on
ip addr add 172.24.2.1/24 dev pxe2-if

# Setup fake IPMI interfaces and vbmc instances
ip addr add 172.24.10.101/24 dev oob-if
vbmc add --address 172.24.10.101 node2
ip addr add 172.24.10.102/24 dev oob-if
vbmc add --address 172.24.10.102 node3

vbmc start

# Setup rules for IP forwarding on PXE networks
echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t nat -A POSTROUTING -o extbr -j MASQUERADE

iptables -A FORWARD -i extbr -o pxe1-if -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i pxe1-if -o extbr -j ACCEPT
iptables -A FORWARD -i extbr -o pxe2-if -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i pxe2-if -o extbr -j ACCEPT

# Setup external ssh access to genesis VM
iptables -t nat -A PREROUTING -p tcp -d 10.23.19.16 --dport 2222 -j DNAT --to-destination 172.24.1.100:22

# Node1 - Genesis
# PXE1 - 172.24.1.100/24
# OOB - 172.24.10.100/24

# Node2 - Master
# PXE1 - 172.24.1.101/24
# vbmc - 172.24.10.101/24

# Node3 - Master
# PXE2 - 172.24.2.101/24
# vbmc - 172.24.10.102/24

