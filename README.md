# UDP Communication and Packet Capture Lab

A hands-on lab demonstrating UDP socket programming, traffic generation, packet capture, and analysis across two virtual machines. This covers the full lifecycle: sending datagrams with Python, capturing them with `tcpdump`, and inspecting the results in Wireshark.

## Project Overview

This project sets up a minimal UDP client-server pair between two Linux VMs on the same network. One VM runs a Python sender that pushes datagrams at one-second intervals; the other runs a Python receiver that binds to a port and prints incoming data. On top of that, we capture raw packets on the wire using `tcpdump` and analyze them offline in Wireshark.

Why bother? Because understanding UDP at the packet level is foundational for:

- **Network debugging** -- figuring out why packets are or aren't arriving, checking payload integrity, spotting port mismatches.
- **Traffic monitoring** -- establishing baselines, detecting anomalies, measuring throughput.
- **Security analysis** -- identifying rogue UDP traffic, DNS exfiltration, amplification attacks.

If you've ever stared at a `tcpdump` output and wondered what you were looking at, this lab is meant to bridge that gap.

## What is UDP?

The User Datagram Protocol is defined in [RFC 768](https://datatracker.ietf.org/doc/html/rfc768) and sits at the transport layer (Layer 4) of the OSI model. It provides a thin wrapper around raw IP, adding just port numbers and an optional checksum. That's about it -- and that minimalism is the whole point.

### Core Characteristics

- **Connectionless**: There is no connection setup. The sender fires off a datagram without first establishing a session with the receiver. No SYN, no SYN-ACK, no state to maintain.
- **No handshake**: Unlike TCP's three-way handshake, UDP has zero round-trip overhead before data transfer begins. The first packet *is* the data.
- **No retransmission**: If a packet is lost in transit, UDP does not know and does not care. There is no acknowledgment mechanism, no retry logic. That responsibility falls to the application, if needed.
- **No ordering guarantees**: Packets may arrive out of order, and UDP makes no attempt to resequence them. A datagram sent second may arrive first.
- **Low latency**: The lack of connection management, acknowledgments, and retransmission timers means UDP introduces minimal delay. For time-sensitive applications, this trade-off is worth it.

### UDP vs TCP at a Glance

| Property | UDP | TCP |
|---|---|---|
| Connection | Connectionless | Connection-oriented (3-way handshake) |
| Reliability | Unreliable -- no delivery guarantee | Reliable -- ACKs, retransmissions |
| Ordering | No ordering | Guaranteed in-order delivery |
| Flow control | None | Sliding window |
| Header size | 8 bytes | 20-60 bytes |
| Overhead | Minimal | Significant |
| Use case | Speed-critical, loss-tolerant | Accuracy-critical |

### Real-World Use Cases

- **DNS** (port 53): Queries are small and need to be fast. A lost query just gets retried by the resolver.
- **Video/audio streaming**: Dropping a frame is preferable to buffering. RTP runs over UDP for this reason.
- **Online gaming**: Player position updates are sent many times per second. A stale packet is useless -- you want the latest one, not a retransmission of an old one.
- **VoIP**: Latency kills call quality more than the occasional dropped sample. UDP keeps the pipeline moving.
- **DHCP, SNMP, TFTP**: All lightweight protocols where TCP's overhead is unnecessary.

### UDP Header Format

The UDP header is exactly 8 bytes, divided into four 16-bit fields:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field | Size | Description |
|---|---|---|
| Source Port | 16 bits | Port number of the sending process. Optional per RFC 768 -- set to zero if unused. Typically used as the reply-to port. |
| Destination Port | 16 bits | Port number on the receiving host. Combined with the destination IP address, this identifies the target socket. |
| Length | 16 bits | Total length of the UDP datagram (header + payload) in bytes. Minimum value is 8 (header only, no payload). |
| Checksum | 16 bits | Covers the header, payload, and a pseudo-header derived from the IP layer. Computed as the 16-bit one's complement of the one's complement sum. Set to `0x0000` if not used (IPv4 only; mandatory in IPv6). |

## Lab Setup

### Environment

Two Linux virtual machines on the same host-only or bridged network:

| Role | Hostname | IP Address | Script |
|---|---|---|---|
| Sender | VM-1 | `192.168.56.101` | `udp_sender.py` |
| Receiver | VM-2 | `192.168.56.102` | `udp_receiver.py` |

Both VMs need Python 3 installed. No additional packages are required -- the scripts use only the `socket` and `time` standard library modules.

### Network Configuration

1. Ensure both VMs are on the same subnet (e.g., `192.168.56.0/24`).
2. Confirm connectivity with a basic `ping` between the two machines.
3. Make sure no firewall rules are blocking UDP traffic on port `9999`.
4. Update the `TARGET_IP` in `udp_sender.py` to point to the receiver VM's IP address.

### How Communication Works

The sender creates a `SOCK_DGRAM` socket and calls `sendto()` in a loop, pushing a message to the receiver's IP and port every second. The receiver binds to `0.0.0.0:9999` and blocks on `recvfrom()`, printing each incoming datagram's source address and payload. There is no connection, no handshake, and no acknowledgment -- exactly what you'd expect from UDP.

## Running the Project

### Start the Receiver (on VM-2)

```bash
python3 udp_receiver.py
```

Expected output:

```
Listening for UDP packets on port 9999...
```

### Start the Sender (on VM-1)

```bash
python3 udp_sender.py
```

Expected output on the sender:

```
Sending UDP packets to 192.168.56.102:9999...

Sent: Packet 1 from sender
Sent: Packet 2 from sender
Sent: Packet 3 from sender
...
```

Expected output on the receiver:

```
Listening for UDP packets on port 9999...

Received from 192.168.56.101:54321 -> Packet 1 from sender
Received from 192.168.56.101:54321 -> Packet 2 from sender
Received from 192.168.56.101:54321 -> Packet 3 from sender
...
```

The source port on the sender side is ephemeral (assigned by the OS), so the exact number will vary.

Stop either script with `Ctrl+C`.

## Generating UDP Traffic (Alternative Method)

If you want to generate quick UDP traffic without running the Python sender, `netcat` (`nc`) works well:

```bash
while true; do echo "UDP TEST PACKET" | nc -u 192.168.56.102 9999; sleep 1; done
```

### Breaking this down

- `while true; do ... done` -- infinite loop.
- `echo "UDP TEST PACKET"` -- produces the payload string on stdout.
- `| nc -u 192.168.56.102 9999` -- pipes that string into netcat. The `-u` flag tells netcat to use UDP instead of its default TCP mode. `192.168.56.102` is the destination IP, `9999` is the destination port.
- `sleep 1` -- pauses for one second between iterations.

Under the hood, each iteration opens a new UDP socket, sends a single datagram containing `UDP TEST PACKET\n`, and closes the socket. The receiver does not need to change -- it sees incoming datagrams the same way regardless of whether they came from the Python script or netcat.

This approach is useful for quick tests when you don't want to deal with a script, or when you want to vary the payload on the fly.

## Capturing UDP Packets

### Method 1: tcpdump (CLI-based packet capture)

`tcpdump` is a command-line packet analyzer that captures traffic directly from a network interface. It works at the kernel level, intercepting packets before they reach (or after they leave) the application layer. This means it captures everything, including headers, regardless of whether an application is listening.

Run this on the **receiver VM** (or any machine on the path):

```bash
sudo tcpdump -i eth0 udp port 9999 -w capture.pcap
```

#### Flag breakdown

| Flag | Meaning |
|---|---|
| `sudo` | Required. `tcpdump` needs root privileges to put the interface into promiscuous mode. |
| `-i eth0` | Listen on the `eth0` interface. Replace with your actual interface name (check with `ip link`). |
| `udp port 9999` | BPF filter expression. Only capture UDP packets where source or destination port is 9999. |
| `-w capture.pcap` | Write raw packet data to `capture.pcap` in pcap format instead of printing to stdout. |

To see packets in real time on the terminal (without saving):

```bash
sudo tcpdump -i eth0 udp port 9999 -n -X
```

- `-n` skips DNS resolution (faster, cleaner output).
- `-X` prints each packet's payload in hex and ASCII.

Stop the capture with `Ctrl+C`. `tcpdump` prints a summary showing how many packets were captured, received by the filter, and dropped by the kernel.

To read a saved capture file later:

```bash
tcpdump -r capture.pcap
```

### Method 2: Python Receiver (Application-layer observation)

The `udp_receiver.py` script itself acts as a basic packet observer. When it calls `recvfrom()`, the kernel hands it the UDP payload and the source address. It then prints this to the console.

However, there are important differences compared to `tcpdump`:

| Aspect | tcpdump | Python receiver |
|---|---|---|
| Layer | Captures at Layer 2/3 (raw frames) | Sees Layer 7 (application payload only) |
| Header visibility | Full Ethernet, IP, and UDP headers | Only payload data + source address/port |
| Dropped packets | Captured even if no app is listening | Not visible -- the kernel discards them silently |
| Malformed packets | Captured and flagged | Never delivered to the socket |
| Performance impact | Minimal (kernel-level BPF) | Subject to Python's GIL and process scheduling |
| Output format | pcap (analyzable in Wireshark) | Plain text on stdout |

The Python receiver tells you what your application actually got. `tcpdump` tells you what was actually on the wire. Both perspectives are valuable, and for serious debugging you want both running simultaneously.

## Analyzing Packets in Wireshark

Transfer `capture.pcap` to a machine with Wireshark installed (e.g., your host OS), then open it:

```
File -> Open -> capture.pcap
```

Or from the command line:

```bash
wireshark capture.pcap
```

### Applying a Display Filter

In the filter bar at the top, enter:

```
udp.port == 9999
```

This filters the view to show only packets matching our lab traffic.

### What to Look For

- **Source/Destination IP**: Confirm the sender and receiver IPs match your VM configuration. Look at the IP layer in the packet detail pane.
- **Ports**: Verify the destination port is `9999`. The source port is ephemeral and will differ per socket or per netcat invocation.
- **Payload**: Expand the "Data" section at the bottom of the packet detail pane. You should see the ASCII text (`Packet 1 from sender`, `UDP TEST PACKET`, etc.) in the hex dump.
- **Packet count and timing**: Check the packet list for gaps in timestamps. If the sender fires every second but you see irregular intervals, something is introducing delay or loss.
- **Packet loss**: Compare the number of packets captured by `tcpdump` against the number of messages printed by the Python receiver. If `tcpdump` shows more packets than the receiver printed, the application dropped some. If both counts match the sender's counter with no gaps, there was no loss. You can also look for ICMP "Destination Unreachable" messages, which indicate the receiver port was not open when packets arrived.

## Observations and Key Learnings

After running this lab, a few things stand out:

1. **UDP is genuinely unreliable.** There is no mechanism at the protocol level to detect or recover from packet loss. If you unplug the network cable for two seconds while the sender is running, those packets are gone. The sender doesn't know, and the receiver never asks.

2. **Packet loss happens silently.** Unlike TCP, where a dropped segment triggers a retransmission timeout and duplicate ACKs, UDP gives you nothing. The only way to detect loss is at the application layer -- by adding sequence numbers or checksums yourself.

3. **No acknowledgments means no backpressure.** The sender will happily blast packets into the void whether the receiver is ready or not. If the receiver's socket buffer fills up, the kernel drops incoming datagrams without notifying anyone.

4. **The performance-reliability trade-off is real.** UDP's 8-byte header and zero round-trip connection setup make it measurably faster than TCP for small, frequent messages. But that speed comes at the cost of every guarantee that TCP provides. For this lab's use case (simple text messages at 1/sec), the difference is negligible. At scale (thousands of packets per second, congested links), it matters a lot.

5. **Application-layer visibility is not the full picture.** What the Python receiver prints and what's actually on the wire can differ. Running `tcpdump` alongside the application gave a ground-truth view of what the network was actually doing.

## Bonus: Going Further

### Simulating Packet Loss

Linux's `tc` (traffic control) utility can introduce artificial packet loss on an interface:

```bash
sudo tc qdisc add dev eth0 root netem loss 20%
```

This drops 20% of outgoing packets randomly. Run the sender and receiver with this active, and you'll see gaps in the received sequence. Remove it with:

```bash
sudo tc qdisc del dev eth0 root netem
```

This is a good way to stress-test any UDP-based application and see how it handles real-world network conditions.

### Adding Sequence Numbers

The sender script already includes a counter (`Packet 1`, `Packet 2`, ...). On the receiver side, you could parse these numbers and track:

- Out-of-order arrivals (sequence number N+1 arrives before N).
- Missing packets (gaps in the sequence).
- Duplicate packets (same sequence number received twice).

This is essentially reinventing a subset of what TCP does automatically -- which is a useful exercise for understanding why TCP exists and what it costs.

## Repository Structure

```
.
├── udp_sender.py       # Sends UDP packets to the receiver VM
├── udp_receiver.py     # Listens for and prints incoming UDP packets
└── README.md           # This file
```

## Requirements

- Python 3.x (standard library only)
- Two networked Linux VMs (VirtualBox, VMware, etc.)
- `tcpdump` (pre-installed on most Linux distributions)
- `netcat` (`nc`) for alternative traffic generation
- Wireshark for pcap analysis (on host or any machine with GUI)

## References

- [RFC 768 -- User Datagram Protocol](https://datatracker.ietf.org/doc/html/rfc768)
- [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/)
- [tcpdump manual page](https://www.tcpdump.org/manpages/tcpdump.1.html)
- [Cloudflare -- What is UDP?](https://www.cloudflare.com/learning/ddos/glossary/user-datagram-protocol-udp/)
