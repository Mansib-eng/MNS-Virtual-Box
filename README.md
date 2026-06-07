# ⚡ MNS VirtualBox — Web-Based VM Manager

> A VirtualBox-like virtualization management platform built with Python, Flask, KVM/QEMU, and libvirt.  
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
13. [References](#-references)

---

## 🎯 Project Overview

**MNS VirtualBox** is a fully functional, web-based virtual machine management application — built from scratch as a course project on cloud and virtualization. It replicates the core functionality of commercial tools like VirtualBox and VMware, while using production-grade Linux virtualization technology (KVM/QEMU) under the hood.

Users can:
- **Create** virtual machines with custom CPU, RAM, and disk settings
- **Start and stop** VMs with a single click
- **Delete** VMs and their associated disk images
- **Monitor** host machine resource usage (CPU, RAM, Disk) in real time
- **View detailed info** of each VM — UUID, VNC port, network config
- **Access VM console** via VNC viewer
- **Manage OS images (ISOs)** for new VM installation
- **Access everything** from a clean professional browser-based dashboard

---

## ⚖️ How It Compares to VirtualBox & AWS EC2

| Feature | VirtualBox | AWS EC2 | **MNS VirtualBox** |
|---|---|---|---|
| Create VMs | ✅ GUI | ✅ Web Console | ✅ Web Dashboard |
| Start / Stop VMs | ✅ | ✅ | ✅ |
| Custom CPU / RAM | ✅ | ✅ | ✅ |
| Custom Disk Size | ✅ | ✅ | ✅ |
| OS Image Upload | ✅ ISO | ✅ AMI | ✅ ISO / IMG |
| Instance Detail Page | ❌ | ✅ | ✅ |
| REST API | ❌ | ✅ | ✅ |
| VNC Console Access | ✅ | ✅ | ✅ |
| Hypervisor | VirtualBox Engine | KVM (Nitro) | **KVM** |
| Management Layer | Qt GUI | React Web App | **Flask Web App** |
| Runs on | Windows/Mac/Linux | AWS Servers | **Ubuntu Linux** |
| Open Source | Partial | ❌ | ✅ |

> **Key Insight:** VirtualBox is simply a UI + management layer sitting on top of its own hypervisor. This project does the exact same thing — a custom UI + management layer on top of KVM, which is a more powerful, production-grade hypervisor built directly into the Linux kernel.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    USER (Browser)                        │
│              http://localhost:5000                       │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP Requests
                           ▼
┌──────────────────────────────────────────────────────────┐
│           FLASK WEB APPLICATION (app.py)                 │
│                                                          │
│  Routes:  /              → Dashboard (list all VMs)      │
│           /vm/<name>     → VM Detail page                │
│           /api/vm/*      → REST API endpoints            │
│           /api/host/stats→ Host resource stats           │
└──────────────────────────┬───────────────────────────────┘
                           │ Python function calls
                           ▼
┌──────────────────────────────────────────────────────────┐
│           VM MANAGER LAYER (vm_manager.py)               │
│                                                          │
│  list_vms()   create_vm()   start_vm()   stop_vm()       │
│  delete_vm()  get_vm_info() get_host_stats() list_isos() │
└──────────────────────────┬───────────────────────────────┘
                           │ libvirt Python API
                           ▼
┌──────────────────────────────────────────────────────────┐
│               LIBVIRT DAEMON (libvirtd)                  │
│                                                          │
│  - Manages VM definitions (XML configs)                  │
│  - Translates API calls to QEMU commands                 │
│  - Handles virtual networking (virbr0)                   │
│  - Runs DHCP server (dnsmasq) for VMs                    │
└──────────────────────────┬───────────────────────────────┘
                           │ QEMU process per VM
                           ▼
┌──────────────────────────────────────────────────────────┐
│               KVM + QEMU HYPERVISOR                      │
│                                                          │
│  KVM  → Uses real CPU hardware (Intel VT-x / AMD-V)      │
│  QEMU → Provides virtual hardware to each VM             │
│         (virtual NIC, virtual disk, virtual display)     │
└──────────────────────────┬───────────────────────────────┘
                           │ Hardware virtualization
                           ▼
┌──────────────────────────────────────────────────────────┐
│         PHYSICAL HARDWARE (Ubuntu 24.04 LTS)             │
│      CPU  │  RAM  │  Storage  │  Network                 │
└──────────────────────────────────────────────────────────┘
```

### Data Flow — Creating a VM

```
User fills form → clicks "🚀 Launch Instance"
        ↓
Progress steps animate: Config → Disk → Network → Done
        ↓
Browser sends POST /api/vm/create {name, ram, cpu, disk, iso}
        ↓
Flask → vm_manager.create_vm()
        ↓
qemu-img create -f qcow2 disk.qcow2 10G
        ↓
virt-install --connect qemu:///system --name vm1 ...
        ↓
libvirtd spawns a QEMU process
        ↓
KVM allocates real CPU + RAM → VM boots
        ↓
Flask returns JSON: {"success": true}
        ↓
Dashboard refreshes → VM appears as "running" ✅
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | HTML5 + CSS3 + Vanilla JS | — | Web dashboard UI |
| **Fonts** | Syne + JetBrains Mono | — | Professional typography |
| **Backend** | Python + Flask | 3.12 / 3.x | Web server & REST API |
| **VM Management** | libvirt-python | 12.x | Python API to control KVM |
| **Hypervisor** | KVM (Kernel-based VM) | Linux kernel built-in | Hardware virtualization |
| **VM Emulation** | QEMU | 8.x | Virtual hardware provider |
| **VM Provisioning** | virt-install | 4.x | VM creation CLI tool |
| **Disk Images** | qcow2 (via qemu-img) | — | Virtual hard disk format |
| **System Stats** | psutil | 5.x | CPU/RAM/Disk monitoring |
| **OS** | Ubuntu | 24.04 LTS | Host operating system |

---

## 🔩 Key Components Explained

### 1. KVM (Kernel-based Virtual Machine)
KVM is a **Type-1 hypervisor** built into the Linux kernel since version 2.6.20. It uses CPU hardware extensions (Intel VT-x or AMD-V) to run virtual machines with near-native performance. Unlike VirtualBox which bundles its own hypervisor, KVM leverages the Linux kernel directly — making it the same technology used by AWS, Google Cloud, and most production cloud providers.

### 2. QEMU (Quick EMUlator)
QEMU provides **virtual hardware** to each VM — a virtual network card, virtual disk controller, virtual USB, virtual display (VNC). While KVM handles fast CPU execution, QEMU handles everything else. Together they are called the KVM/QEMU stack.

### 3. libvirt
libvirt is a **virtualization management API** that provides a clean, unified interface to manage KVM, QEMU, Xen, and other hypervisors. Instead of running raw QEMU commands, the application uses the `libvirt-python` library to create, start, stop, and query VMs. The `libvirtd` daemon runs in the background and manages all VM state.

### 4. qcow2 Disk Format
Each virtual machine gets its own `.qcow2` disk image file stored in `~/my-virtualbox/disks/`. QCOW2 (QEMU Copy-On-Write version 2) is the standard virtual disk format — equivalent to VirtualBox's `.vdi` or VMware's `.vmdk`. It supports sparse allocation, snapshots, and compression.

### 5. Flask
Flask handles all HTTP routing — serving HTML pages and JSON API responses. It connects the browser frontend to the Python VM management code.

### 6. Virtual Networking
libvirt creates a **virtual network bridge** (`virbr0`) on the host and runs a DHCP server (dnsmasq) to give VMs IP addresses in the `192.168.122.x` range. VMs reach the internet via NAT through the host.

---

## ✅ Prerequisites

### Hardware Requirements

| Resource | Minimum | Used In This Project |
|---|---|---|
| CPU | 4 cores with VT-x/AMD-V | HP EliteBook 840 G6 |
| RAM | 8 GB | 8 GB |
| Disk | 50 GB free | Available storage |
| OS | Ubuntu 20.04+ | **Ubuntu 24.04 LTS** ✅ |

### Verify KVM Support

```bash
# Check CPU virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo
# Result: 1 or more = SUPPORTED ✅

# Full KVM check
sudo apt install -y cpu-checker
sudo kvm-ok
# Expected: "KVM acceleration can be used" ✅
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
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virtinst \
    virt-manager \
    libguestfs-tools \
    python3-pip \
    python3-venv \
    cpu-checker \
    pkg-config \
    libvirt-dev \
    python3-dev \
    build-essential
```

| Package | Purpose |
|---|---|
| `qemu-kvm` | KVM-accelerated QEMU — core VM engine |
| `libvirt-daemon-system` | libvirt background service |
| `libvirt-clients` | `virsh` command-line tool |
| `bridge-utils` | Virtual network bridges for VMs |
| `virtinst` | `virt-install` VM creation tool |
| `pkg-config` | Required to compile libvirt-python |
| `libvirt-dev` | C headers for libvirt-python compilation |
| `build-essential` | GCC compiler for Python C extensions |

### Step 3 — Add User to Groups

```bash
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
newgrp libvirt
```

### Step 4 — Start libvirt Service

```bash
sudo systemctl enable --now libvirtd
sudo systemctl status libvirtd
# Expected: active (running) ✅
```

### Step 5 — Fix Permissions for KVM Access

```bash
sudo chmod o+x /home/$USER
sudo chmod -R o+rw ~/my-virtualbox/disks
sudo chmod -R o+rx ~/my-virtualbox/iso
```

### Step 6 — Setup Project Folder and Python Environment

Place the project source files inside `~/my-virtualbox/`.

```bash
cd ~
mkdir -p my-virtualbox
cd my-virtualbox

# Create runtime folders. These are not included in the submitted ZIP.
mkdir -p disks iso

python3 -m venv venv
source venv/bin/activate

# Recommended: install dependencies from requirements.txt
pip install -r requirements.txt
```

If `libvirt-python` fails to install, make sure these system packages were installed in Step 2:

```bash
sudo apt install -y pkg-config libvirt-dev python3-dev build-essential
source ~/my-virtualbox/venv/bin/activate
pip install libvirt-python
```

### Step 7 — Add OS Images

```bash
cd ~/my-virtualbox/iso

# Lightweight test image (20MB) — recommended for testing
wget https://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img

# Ubuntu Server ISO (2GB) — for real VMs
wget https://releases.ubuntu.com/22.04.4/ubuntu-22.04.4-live-server-amd64.iso
```

---

## 🚀 Running the Application

```bash
cd ~/my-virtualbox
source venv/bin/activate
python app.py
```

Expected output:
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

Open browser:
```
http://localhost:5000
```

---

## 🖥️ Features & Usage

### Dashboard (`/`)
- Real-time host stats — CPU usage, RAM, Disk with progress bars
- VM count — total and currently running
- VM table — name, status badge, resource chips, action buttons
- Click **🔍 Details** to open the VM detail page
- Click **＋ New VM** to create a virtual machine

### VM Detail Page (`/vm/<name>`)
- Full VM configuration — vCPUs, RAM, architecture, hypervisor
- Network info — NAT network, virtio-net interface
- VNC console access — port number + copy command button
- UUID — unique identifier, copyable
- How-to-connect guide (shown only when VM is running)
- Start / Stop / Delete controls

### Creating a Virtual Machine
1. Click **＋ New VM**
2. Fill in Name, RAM, vCPUs, Disk, ISO
3. Click **🚀 Launch Instance**
4. Watch the animated progress steps: Config → Disk → Network → Done ✅

### VM Actions
| Action | Behavior |
|---|---|
| **▶ Start** | Boots the VM, button shows spinner while starting |
| **⏹ Stop** | Graceful shutdown, waits 30s then force-stops |
| **🗑 Delete** | Double confirmation, removes VM + disk file |
| **🔍 Details** | Opens full VM detail page |

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/vms` | List all VMs as JSON |
| `POST` | `/api/vm/create` | Create a new VM |
| `POST` | `/api/vm/<name>/start` | Start a VM |
| `POST` | `/api/vm/<name>/stop` | Stop a VM |
| `DELETE` | `/api/vm/<name>/delete` | Delete a VM |
| `GET` | `/api/host/stats` | Host CPU/RAM/Disk stats |

### Example Requests

```bash
# List all VMs
curl http://localhost:5000/api/vms

# Create a VM
curl -X POST http://localhost:5000/api/vm/create \
  -H "Content-Type: application/json" \
  -d '{"name":"test-vm","ram_mb":2048,"vcpus":2,"disk_gb":10}'

# Start a VM
curl -X POST http://localhost:5000/api/vm/test-vm/start

# Stop a VM
curl -X POST http://localhost:5000/api/vm/test-vm/stop \
  -H "Content-Type: application/json" \
  -d '{"force": false}'

# Delete a VM
curl -X DELETE http://localhost:5000/api/vm/test-vm/delete

# Host stats
curl http://localhost:5000/api/host/stats
```

---

## 📁 Project File Structure

```
my-virtualbox/
│
├── README.md               # Project documentation
├── app.py                  # Flask web app — all routes & API endpoints
├── vm_manager.py           # Core VM engine — all libvirt operations
├── requirements.txt        # Python dependencies
│
├── templates/
│   ├── index.html          # Main dashboard — VM list & stats
│   └── vm_detail.html      # Single VM detail page
│
├── iso/                    # Runtime folder: place .iso/.img files here
│   └── (download OS images here; do not submit large images)
│
├── disks/                  # Runtime folder: VM disk images are auto-created
│   └── <vm-name>.qcow2
│
└── venv/                   # Local Python virtual environment; do not submit
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

TYPE 1 — KVM (used in this project)
┌──────────────────────────┐
│      Virtual Machine     │
├──────────────────────────┤
│  KVM (in Linux kernel)   │  ← runs directly on hardware
├──────────────────────────┤
│      Hardware            │
└──────────────────────────┘
```

KVM is faster and more efficient — it's the same technology used by AWS, Google Cloud, and Azure internally.

### What Happens When You Start a VM

```
1. libvirt reads VM XML config from /etc/libvirt/qemu/
2. libvirt launches a QEMU process with correct parameters
3. QEMU creates virtual hardware (NIC, disk, display)
4. KVM maps virtual CPU to real CPU via Intel VT-x
5. VM OS boots inside its virtual hardware environment
6. Disk reads/writes go to the .qcow2 file on host disk
7. Network traffic routes through virbr0 bridge via NAT
```

---


## 📖 References

- [KVM Official Documentation](https://www.linux-kvm.org/page/Documents)
- [libvirt Documentation](https://libvirt.org/docs.html)
- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Ubuntu Server Guide — KVM](https://ubuntu.com/server/docs/virtualization-kvm)
- [libvirt Python API Reference](https://libvirt.org/python.html)

---

## 👤 Author

**Student Name:** *Ibnul Mansib*  
**Student ID:** *2020331061*  
**Course:** Cloud Computing Lab  
**Submission Date:** *(Date)*  
**Institution:** *Shahjalal University of Science and Technology*  
**Host Machine:** HP EliteBook 840 G6 — Ubuntu 24.04 LTS  

---
