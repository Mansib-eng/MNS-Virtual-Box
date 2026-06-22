# ⚡ MNS VirtualBox — EC2-Style VM Manager

> A VirtualBox-like virtualization management platform with EC2-style features,
> real-time updates, and hardware-aware provisioning.
> Built with Python, Flask, KVM/QEMU, and libvirt on Ubuntu 24.04 LTS.
> **Course Project — Cloud Lab Evaluation**

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [How It Compares to VirtualBox & AWS EC2](#-how-it-compares-to-virtualbox--aws-ec2)
3. [System Architecture](#-system-architecture)
4. [Technology Stack](#-technology-stack)
5. [Key Components Explained](#-key-components-explained)
6. [Prerequisites](#-prerequisites)
7. [Installation Guide](#-installation-guide)
8. [Running the Application](#-running-the-application)
9. [Features & Usage](#-features--usage)
10. [API Reference](#-api-reference)
11. [Project File Structure](#-project-file-structure)
12. [How Virtualization Works](#-how-virtualization-works-under-the-hood)
13. [Troubleshooting](#-troubleshooting)
14. [References](#-references)

---

## 🎯 Project Overview

**MNS VirtualBox** is a fully functional, web-based virtual machine management
platform built from scratch as a Cloud Lab Evaluation course project. It combines:

- **VirtualBox-like engine** — uses KVM/QEMU/libvirt, the same production-grade
  virtualization stack used inside AWS, Google Cloud, and Azure
- **EC2-style interface** — launch, stop, reboot, snapshot, and manage VMs from
  a web dashboard, just like AWS EC2
- **Real-time updates** — Server-Sent Events (SSE) push live VM state changes
  to the browser instantly, without any page reload
- **Hardware-aware provisioning** — detects available CPU, RAM, and disk before
  VM creation and warns the user, just like EC2 quota checks

Built using **AI-assisted development** (Claude by Anthropic) as permitted by the
project brief: *"You can use any LLMs to build it."*

---

## ⚖️ How It Compares to VirtualBox & AWS EC2

| Feature | VirtualBox | AWS EC2 | **MNS VirtualBox** |
|---|---|---|---|
| Launch VMs | ✅ GUI | ✅ Web Console | ✅ Web Dashboard |
| Start / Stop | ✅ | ✅ | ✅ |
| Reboot | ✅ | ✅ | ✅ |
| Pause / Resume | ✅ | ✅ | ✅ |
| Custom CPU / RAM | ✅ | ✅ | ✅ |
| Custom Disk Size | ✅ | ✅ | ✅ |
| OS Image Support | ✅ ISO | ✅ AMI | ✅ ISO / IMG / QCOW2 |
| AMI-style image catalog | ❌ | ✅ | ✅ |
| Instance Detail Page | ❌ | ✅ | ✅ |
| UUID / Instance ID | ❌ | ✅ | ✅ |
| MAC Address | ❌ | ✅ | ✅ |
| Guest IP Detection | ❌ | ✅ | ✅ |
| Snapshots | ✅ | ✅ | ✅ |
| VNC Console Access | ✅ | ✅ | ✅ |
| Real-time SSE Updates | ❌ | ✅ | ✅ |
| Hardware Limit Warnings | ❌ | ✅ | ✅ |
| REST API | ❌ | ✅ | ✅ |
| Backend Validation | ❌ | ✅ | ✅ |
| Dynamic Resource Limits | ❌ | ✅ | ✅ |
| Hypervisor | VirtualBox Engine | KVM (Nitro) | **KVM / QEMU** |
| Management Layer | Qt GUI | React Web App | **Flask Web App** |
| Runs on | Windows/Mac/Linux | AWS Servers | **Ubuntu 24.04 LTS** |
| Open Source | Partial | ❌ | ✅ |

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    USER (Browser)                        │
│     http://localhost:5000   or   http://127.0.0.1:5000   │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP + SSE (persistent stream)
                           ▼
┌──────────────────────────────────────────────────────────┐
│           FLASK WEB APPLICATION (app.py)                 │
│                                                          │
│  Pages:   /              → Dashboard (VM list + stats)   │
│           /vm/<name>     → VM Detail page (EC2-style)    │
│                                                          │
│  SSE:     /api/events    → Real-time event stream        │
│                            pushes VM state changes       │
│                            every 3 seconds               │
│                                                          │
│  API:     /api/vm/create          → Create VM            │
│           /api/vm/<n>/start       → Start VM             │
│           /api/vm/<n>/stop        → Stop VM              │
│           /api/vm/<n>/reboot      → Reboot VM            │
│           /api/vm/<n>/pause       → Pause VM             │
│           /api/vm/<n>/resume      → Resume VM            │
│           /api/vm/<n>/delete      → Delete VM            │
│           /api/vm/<n>/ip          → Get Guest IP         │
│           /api/vm/<n>/snapshots   → List Snapshots       │
│           /api/vm/<n>/snapshot/create  → Take Snapshot   │
│           /api/vm/<n>/snapshot/<s>/restore → Restore     │
│           /api/vm/<n>/snapshot/<s>/delete  → Delete      │
│           /api/host/stats         → Host resource stats  │
│           /api/host/limits        → Dynamic limits       │
│           /api/images             → Available images     │
└──────────────────────────┬───────────────────────────────┘
                           │ Python function calls
                           ▼
┌──────────────────────────────────────────────────────────┐
│           VM MANAGER LAYER (vm_manager.py)               │
│                                                          │
│  create_vm()      validate_vm_params()  detect_os_variant│
│  start_vm()       stop_vm()             delete_vm()      │
│  reboot_vm()      pause_vm()            resume_vm()      │
│  get_vm_info()    get_guest_ip()        get_host_stats() │
│  create_snapshot() list_snapshots()    restore_snapshot()│
│  delete_snapshot() get_dynamic_limits() list_images()    │
│  list_isos()      (with clean display names)             │
└──────────────────────────┬───────────────────────────────┘
                           │ libvirt Python API
                           ▼
┌──────────────────────────────────────────────────────────┐
│               LIBVIRT DAEMON (libvirtd)                  │
│  - Manages VM XML configs (/etc/libvirt/qemu/)           │
│  - Translates API calls to QEMU/KVM commands             │
│  - Handles virtual networking (virbr0 bridge)            │
│  - Runs DHCP server (dnsmasq) for VM IPs                 │
│  - Manages VM snapshots                                  │
└──────────────────────────┬───────────────────────────────┘
                           │ QEMU process per VM
                           ▼
┌──────────────────────────────────────────────────────────┐
│               KVM + QEMU HYPERVISOR                      │
│  KVM  → Uses real CPU hardware (Intel VT-x)              │
│  QEMU → Provides virtual hardware to each VM             │
│         (virtual NIC, virtual disk, VNC display)         │
└──────────────────────────┬───────────────────────────────┘
                           │ Hardware virtualization
                           ▼
┌──────────────────────────────────────────────────────────┐
│    HP EliteBook 840 G6 — Ubuntu 24.04 LTS (Physical)     │
│         CPU  │  RAM  │  NVMe Storage  │  Network         │
└──────────────────────────────────────────────────────────┘
```

### How Real-Time SSE Works

```
Browser opens ONE persistent connection to /api/events
        ↓
Server checks VM states every 3 seconds
        ↓
If ANY VM state changed → push JSON update to browser
        ↓
Browser receives data → updates badge, buttons, stats
        ↓
NO page reload needed — instant live update ✅

Example: VM goes from running → stopped
  Server detects change (within 3s)
  Pushes: {"vms": [{"name":"test-1","state":"stopped"}], ...}
  Browser: changes badge from ● running → ● stopped
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | HTML5 + CSS3 + Vanilla JS | — | Web dashboard UI |
| **Real-time** | Server-Sent Events (SSE) | Browser native | Live VM state updates |
| **Fonts** | Syne + JetBrains Mono | — | Professional typography |
| **Backend** | Python + Flask | 3.12 / 3.x | Web server & REST API |
| **VM Management** | libvirt-python | 12.x | Python API to control KVM |
| **Hypervisor** | KVM (Kernel-based VM) | Linux built-in | Hardware virtualization |
| **VM Emulation** | QEMU | 8.x | Virtual hardware provider |
| **VM Provisioning** | virt-install | 4.x | VM creation CLI tool |
| **Disk Images** | qcow2 via qemu-img | — | Virtual hard disk format |
| **Disk Info** | virsh domblkinfo | — | Disk size while VM running |
| **System Stats** | psutil | 5.x | Host CPU/RAM/Disk monitoring |
| **OS** | Ubuntu | 24.04 LTS | Host operating system |
| **Hardware** | HP EliteBook 840 G6 | — | Physical host machine |

---

## 🔩 Key Components Explained

### 1. KVM (Kernel-based Virtual Machine)
KVM is a **Type-1 hypervisor** built into the Linux kernel. It uses CPU hardware
extensions (Intel VT-x on the EliteBook 840 G6) to run VMs with near-native
performance. This is the same technology used by AWS, Google Cloud, and Azure.

### 2. QEMU (Quick EMUlator)
QEMU provides **virtual hardware** to each VM — a virtual network card, virtual
disk controller, and VNC display. KVM handles fast CPU execution, QEMU handles
device emulation. Together they are the KVM/QEMU stack.

### 3. libvirt
A **virtualization management API** providing a unified interface to manage KVM.
The application uses `libvirt-python` to create, start, stop, snapshot, and query
VMs. The `libvirtd` daemon runs in the background managing all VM state.

### 4. Server-Sent Events (SSE)
SSE is a web technology where the **server pushes data to the browser** over a
single persistent HTTP connection. Unlike WebSockets (bidirectional), SSE is
one-way (server → browser), which is perfect for live status updates. The browser
connects once to `/api/events` and receives VM state changes as they happen,
without polling or page reloads. This is exactly how AWS EC2 console updates work.

### 5. Hardware Warning System
When the user opens the Create VM modal, the frontend calls `/api/host/limits`
to get real-time CPU, RAM, and disk availability. It then:
- Shows available resources under each input field (green/orange/red)
- Displays a warning box if resources are low
- Automatically sets input maximums to prevent over-provisioning
- Updates disk size field to available maximum

### 6. AMI-Style Image Catalog
Like AWS AMI (Amazon Machine Image), the application shows clean OS names instead
of raw filenames. A `NAME_MAP` in `list_isos()` maps filename keywords to display
names with OS emoji indicators:
```
cirros-0.6.2-x86_64-disk.img  →  🟠 CirrOS — Test Image · 20.4 MB · IMG
ubuntu-22.04.4-live-server...  →  🟣 Ubuntu Server 22.04 LTS · 2006 MB · ISO
debian-12-generic-amd64.qcow2 →  🔴 Debian 12 (Bookworm) · 400 MB · QCOW2
alpine-virt-3.19.0-x86_64.iso →  🔷 Alpine Linux · 60 MB · ISO
```

### 7. qcow2 Disk Format
Each VM gets its own `.qcow2` disk image in `disks/`. Disk info is read via
`virsh domblkinfo` while the VM is running (since QEMU holds a write lock on
the disk file during VM execution, making direct `qemu-img info` fail).

### 8. Snapshots (EC2-style)
Snapshots use libvirt's `snapshotCreateXML` API. Users can take, restore, and
delete snapshots from the VM detail page — identical to EC2 snapshot workflow.

---

## ✅ Prerequisites

### Hardware Requirements

| Resource | Minimum | This Project |
|---|---|---|
| CPU | 4 cores with Intel VT-x / AMD-V | HP EliteBook 840 G6 (Intel) |
| RAM | 8 GB | 8 GB |
| Disk | 50 GB free | NVMe storage |
| OS | Ubuntu 20.04+ | **Ubuntu 24.04 LTS** ✅ |

### Verify KVM Support

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo   # 1 or more = supported ✅
sudo apt install -y cpu-checker
sudo kvm-ok                           # "KVM acceleration can be used" ✅
```

---

## 📦 Installation Guide

### Step 1 — System Update

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2 — Install KVM, QEMU, and libvirt

```bash
sudo apt install -y \
    qemu-kvm libvirt-daemon-system libvirt-clients \
    bridge-utils virtinst virt-manager libguestfs-tools \
    python3-pip python3-venv cpu-checker \
    pkg-config libvirt-dev python3-dev build-essential
```

### Step 3 — Add User to Groups

```bash
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
newgrp libvirt
```

### Step 4 — Start libvirt Service

```bash
sudo systemctl enable --now libvirtd
sudo systemctl status libvirtd   # Expected: active (running) ✅
```

### Step 5 — Fix Permissions

```bash
sudo chmod o+x /home/$USER
sudo chown -R $USER:libvirt ~/my-virtualbox/disks
sudo chown -R $USER:libvirt ~/my-virtualbox/iso
sudo chmod -R 775 ~/my-virtualbox/disks
sudo chmod -R 775 ~/my-virtualbox/iso
```

### Step 6 — Setup Python Environment

```bash
cd ~
mkdir my-virtualbox && cd my-virtualbox
mkdir -p disks iso templates

python3 -m venv venv
source venv/bin/activate
pip install flask libvirt-python psutil Pillow requests
```

### Step 7 — Add OS Images

```bash
cd ~/my-virtualbox/iso

# CirrOS — tiny test image (20 MB) — for quick testing
wget https://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img

# Alpine Linux — minimal ISO (60 MB)
wget https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.0-x86_64.iso

# Debian 12 cloud image (400 MB)
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2

# Ubuntu 24.04 cloud image (700 MB)
wget https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img

# Ubuntu Server 22.04 ISO (2 GB) — full installer
wget https://releases.ubuntu.com/22.04.4/ubuntu-22.04.4-live-server-amd64.iso
```

### Step 8 — Start Default Virtual Network

```bash
sudo virsh net-start default
sudo virsh net-autostart default
virsh net-list --all   # Expected: default active yes yes ✅
```

---

## 🚀 Running the Application

```bash
cd ~/my-virtualbox
source venv/bin/activate
python app.py
```

Open browser: `http://localhost:5000`

---

## 🖥️ Features & Usage

### Dashboard (`/`)
- **Real-time stats** — CPU, RAM, Disk update live via SSE (no reload needed)
- **Live VM status** — badges change instantly when VM state changes
- **Running status dot** — turns orange when SSE reconnecting, green when connected
- Click **🔍 VM name** to open EC2-style detail page
- Click **＋ New VM** to open hardware-aware create modal

### Create VM Modal — Hardware Aware
When opened, automatically:
- Fetches real-time resource availability from `/api/host/limits`
- Shows available RAM in green/orange/red under RAM input
- Shows available CPU cores under vCPUs input
- Shows available disk space under Disk input
- Sets input maximums to prevent over-provisioning
- Shows `⚠ Hardware Limitations Detected` warning if resources are low
- Displays AMI-style image names with emoji and size info

### VM Detail Page (`/vm/<name>`) — EC2-style
- Large stat cards — vCPUs, RAM, Instance State
- VM Configuration — name, state, architecture, machine type (from real XML)
- Storage — disk format, real disk size, disk path, MAC, Guest IP, VNC
- Instance Identifier — full UUID with copy button
- Snapshots — take, restore, delete (EC2 snapshot style)
- How to Connect — VNC install + connection command
- Action buttons — Stop, Reboot, Pause/Resume, Delete

### VM Lifecycle Actions
| Action | Behavior |
|---|---|
| **▶ Start** | Powers on VM, spinner while starting |
| **⏹ Stop** | Graceful shutdown (30s timeout then force) |
| **🔄 Reboot** | Sends reboot signal to VM OS |
| **⏸ Pause** | Freezes VM in memory (suspend) |
| **▶ Resume** | Unfreezes paused VM |
| **🗑 Delete** | Double confirmation, removes VM + disk |
| **📸 Snapshot** | Creates named snapshot of current state |
| **↩ Restore** | Reverts VM to chosen snapshot |

### Real-Time SSE Updates
The dashboard maintains a **persistent connection** to `/api/events`. When any
VM changes state (start/stop/pause), the server pushes the update and the browser:
- Updates the status badge colour and text
- Swaps Start ↔ Stop button
- Updates Running count in stat card
- Updates CPU/RAM/Disk stats
- All without any page reload

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/events` | SSE stream — real-time VM state updates |
| `GET` | `/api/vms` | List all VMs |
| `POST` | `/api/vm/create` | Create a new VM |
| `POST` | `/api/vm/<name>/start` | Start a VM |
| `POST` | `/api/vm/<name>/stop` | Stop a VM |
| `POST` | `/api/vm/<name>/reboot` | Reboot a VM |
| `POST` | `/api/vm/<name>/pause` | Pause a VM |
| `POST` | `/api/vm/<name>/resume` | Resume a VM |
| `DELETE` | `/api/vm/<name>/delete` | Delete a VM |
| `GET` | `/api/vm/<name>/ip` | Get guest IP address |
| `GET` | `/api/vm/<name>/snapshots` | List snapshots |
| `POST` | `/api/vm/<name>/snapshot/create` | Take a snapshot |
| `POST` | `/api/vm/<name>/snapshot/<s>/restore` | Restore snapshot |
| `DELETE` | `/api/vm/<name>/snapshot/<s>/delete` | Delete snapshot |
| `GET` | `/api/host/stats` | Host CPU/RAM/Disk stats |
| `GET` | `/api/host/limits` | Dynamic resource limits |
| `GET` | `/api/images` | Available boot images with clean names |

---

## 📁 Project File Structure

```
my-virtualbox/
│
├── app.py                  # Flask app — all routes, API endpoints, SSE stream
│
├── vm_manager.py           # Core VM engine — all libvirt operations
│                           # Validation, image handling, OS detection,
│                           # snapshots, guest IP, disk size via domblkinfo
│
├── requirements.txt        # Python dependencies
│
├── templates/
│   ├── index.html          # Dashboard — VM list, live stats, SSE client,
│   │                       # hardware-aware create modal, AMI image names
│   └── vm_detail.html      # EC2-style VM detail — snapshots, VNC, UUID
│
├── iso/                    # Boot images
│   ├── cirros-0.6.2-x86_64-disk.img
│   ├── alpine-virt-3.19.0-x86_64.iso
│   ├── debian-12-generic-amd64.qcow2
│   ├── ubuntu-24.04-server-cloudimg-amd64.img
│   └── ubuntu-22.04.4-live-server-amd64.iso
│
├── disks/                  # VM disk images (auto-created)
│   └── <vm-name>.qcow2
│
└── venv/                   # Python virtual environment
```

---

## 🔬 How Virtualization Works (Under the Hood)

### Type 1 vs Type 2 Hypervisors

```
TYPE 2 — VirtualBox, VMware Workstation
┌──────────────────────────┐
│      Virtual Machine     │
├──────────────────────────┤
│   Hypervisor (as app)    │  ← runs inside host OS
├──────────────────────────┤
│      Host OS             │
├──────────────────────────┤
│      Hardware            │
└──────────────────────────┘

TYPE 1 — KVM (used in MNS VirtualBox)
┌──────────────────────────┐
│      Virtual Machine     │
├──────────────────────────┤
│  KVM (in Linux kernel)   │  ← runs directly on hardware
├──────────────────────────┤
│      Hardware            │
└──────────────────────────┘
```

KVM is faster and more efficient — same technology used by AWS, Google, Azure.

### What Happens When You Start a VM

```
1. libvirt reads VM XML from /etc/libvirt/qemu/<name>.xml
2. libvirt launches a QEMU process with correct parameters
3. QEMU creates virtual hardware (NIC, disk, VNC display)
4. KVM maps virtual CPU to real CPU via Intel VT-x
5. VM OS boots inside its virtual environment
6. Disk reads/writes go to the .qcow2 file on host disk
7. Network traffic routes through virbr0 bridge via NAT
8. VNC server on port 5900 exposes the VM screen
9. SSE stream detects state change and notifies browser
```

### How SSE Real-Time Updates Work

```
1. Browser loads dashboard page
2. JavaScript calls: new EventSource('/api/events')
3. Flask opens a streaming response (generator function)
4. Every 3 seconds: server checks all VM states
5. If state changed: server yields JSON data event
6. Browser EventSource receives event automatically
7. JavaScript updates only the changed DOM elements
8. No page reload, no flicker, instant feedback
```

---

## 🔧 Troubleshooting

### libvirtd not running
```bash
sudo systemctl restart libvirtd && sudo systemctl status libvirtd
```

### Permission denied on disk/iso
```bash
sudo chown -R $USER:libvirt ~/my-virtualbox/disks
sudo chmod -R 775 ~/my-virtualbox/disks
```

### Network not found error
```bash
sudo virsh net-start default && sudo virsh net-autostart default
```

### VM stuck after failed creation
```bash
virsh --connect qemu:///system destroy <vm-name> 2>/dev/null
virsh --connect qemu:///system undefine <vm-name> 2>/dev/null
rm -f ~/my-virtualbox/disks/<vm-name>.qcow2
```

### Disk size shows — GB (disk locked by running VM)
```bash
virsh --connect qemu:///system domblkinfo <vm-name> \
  ~/my-virtualbox/disks/<vm-name>.qcow2 --human
```

### SSE not connecting (check browser console)
```bash
# Verify SSE endpoint works
curl -N http://localhost:5000/api/events
# Should stream data every 3 seconds
```

### libvirt-python install fails
```bash
deactivate
sudo apt install -y pkg-config libvirt-dev python3-dev build-essential
source ~/my-virtualbox/venv/bin/activate
pip install libvirt-python
```

### Port 5000 in use
```bash
sudo lsof -i :5000 && sudo kill <PID>
```

---

## 📖 References

- [KVM Official Documentation](https://www.linux-kvm.org/page/Documents)
- [libvirt Documentation](https://libvirt.org/docs.html)
- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MDN — Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Ubuntu Server Guide — KVM](https://ubuntu.com/server/docs/virtualization-kvm)
- [libvirt Python API Reference](https://libvirt.org/python.html)
- [virsh Command Reference](https://libvirt.org/manpages/virsh.html)

---

## 👤 Author

**Student Name:** *(Your Name)*
**Student ID:** *(Your Student ID)*
**Course:** Cloud Computing / Virtualization Lab
**Submission Date:** June 2026
**Institution:** *(Your University / College)*
**Host Machine:** HP EliteBook 840 G6 — Ubuntu 24.04 LTS (Noble)

---

## 📝 Note on AI Assistance

This project was built with the assistance of **Claude (Anthropic)** for code
generation, debugging, and architecture guidance, as explicitly permitted by the
course project brief:

> *"You can use any LLMs to build it."*

All code was reviewed, understood, tested, and deployed by the student on a
physical Ubuntu 24.04 machine with real KVM virtualization.

---

*Built with ❤️ using Python · Flask · KVM · QEMU · libvirt · SSE on Ubuntu 24.04 LTS*
