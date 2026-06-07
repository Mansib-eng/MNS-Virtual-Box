import libvirt
import os
import subprocess
import xml.etree.ElementTree as ET
import json

# Directory to store VM disk images
DISK_DIR = os.path.expanduser("~/my-virtualbox/disks")
ISO_DIR  = os.path.expanduser("~/my-virtualbox/iso")

# Create directories if they don't exist
os.makedirs(DISK_DIR, exist_ok=True)
os.makedirs(ISO_DIR,  exist_ok=True)


def get_connection():
    """Connect to local KVM hypervisor"""
    conn = libvirt.open('qemu:///system')
    if conn is None:
        raise Exception("Failed to connect to KVM")
    return conn


def list_vms():
    """List all VMs (running + stopped)"""
    conn = get_connection()
    vms = []

    # Get running VMs
    for dom in conn.listAllDomains():
        info = dom.info()
        # State codes: 1=running, 3=paused, 5=shut off
        state_map = {
            0: 'no state',
            1: 'running',
            2: 'blocked',
            3: 'paused',
            4: 'shutting down',
            5: 'stopped',
            6: 'crashed'
        }
        vms.append({
            'name':   dom.name(),
            'state':  state_map.get(info[0], 'unknown'),
            'ram_mb': info[2] // 1024,   # Convert KB to MB
            'vcpus':  info[3],
            'id':     dom.ID() if dom.ID() != -1 else 'N/A'
        })

    conn.close()
    return vms


def create_vm(name, ram_mb, vcpus, disk_gb, iso_path=None):
    """
    Create a new Virtual Machine
    name     : VM name (e.g. 'ubuntu-vm-1')
    ram_mb   : RAM in megabytes (e.g. 1024 for 1GB)
    vcpus    : Number of virtual CPUs
    disk_gb  : Disk size in gigabytes
    iso_path : Path to OS ISO file (optional)
    """

    disk_path = os.path.join(DISK_DIR, f"{name}.qcow2")

    # Step 1: Create virtual disk image (only if not using .img file)
    if not (iso_path and iso_path.endswith('.img')):
        subprocess.run([
            'qemu-img', 'create',
            '-f', 'qcow2',
            disk_path,
            f'{disk_gb}G'
        ], check=True)

    # Step 2: Build the VM install command
    cmd = [
        'virt-install',
	'--connect',     'qemu:///system',
        '--name',        name,
        '--ram',         str(ram_mb),
        '--vcpus',       str(vcpus),
        '--disk',        f'path={disk_path},format=qcow2',
        '--os-variant',   'ubuntu22.04',
        '--network',     'network=default',
        '--graphics',    'vnc,listen=0.0.0.0',
        '--noautoconsole',
    ]

    # .img = pre-installed image, boot directly
    # .iso = installer disc, boot from cdrom
    if iso_path and os.path.exists(iso_path):
        if iso_path.endswith('.img'):
            # Copy img as the disk instead of creating blank disk
            subprocess.run([
                'cp', iso_path, disk_path
            ], check=True)
            cmd += ['--import', '--boot', 'hd']
        else:
            cmd += ['--cdrom', iso_path]
    else:
        cmd += ['--import', '--boot', 'hd']

    # Step 3: Run the command to create VM
    subprocess.run(cmd, check=True)

    return {'status': 'created', 'name': name, 'disk': disk_path}


def start_vm(name):
    """Start (power on) a VM"""
    conn = get_connection()
    dom  = conn.lookupByName(name)
    dom.create()   # 'create' in libvirt means 'start'
    conn.close()
    return {'status': 'started', 'name': name}


def stop_vm(name, force=False):
    """Stop a VM - graceful first, force if needed"""
    import time
    conn = get_connection()
    dom  = conn.lookupByName(name)

    if force:
        dom.destroy()
        conn.close()
        return {'status': 'force stopped', 'name': name}

    # Try graceful shutdown first
    dom.shutdown()

    # Wait up to 30 seconds for graceful shutdown
    for i in range(30):
        time.sleep(1)
        # Refresh domain info
        try:
            dom = conn.lookupByName(name)
            state = dom.info()[0]
            # State 5 = shut off
            if state == 5:
                conn.close()
                return {'status': 'stopped', 'name': name}
        except:
            # VM no longer exists = stopped
            conn.close()
            return {'status': 'stopped', 'name': name}

    # Still running after 30 seconds = force stop
    try:
        dom.destroy()
    except:
        pass

    conn.close()
    return {'status': 'force stopped after timeout', 'name': name}


def delete_vm(name, delete_disk=True):
    """Delete a VM permanently"""
    conn = get_connection()
    dom  = conn.lookupByName(name)

    # If running, force stop first
    if dom.isActive():
        dom.destroy()

    # Get disk path from VM XML config before deleting
    xml  = dom.XMLDesc()
    root = ET.fromstring(xml)
    disk_path = None
    for disk in root.findall('.//disk[@device="disk"]/source'):
        disk_path = disk.get('file')

    # Undefine (delete) the VM from KVM
    dom.undefine()

    # Delete the disk image file
    if delete_disk and disk_path and os.path.exists(disk_path):
        os.remove(disk_path)

    conn.close()
    return {'status': 'deleted', 'name': name}


def get_vm_info(name):
    """Get detailed info about a single VM"""
    conn = get_connection()
    dom  = conn.lookupByName(name)
    info = dom.info()

    state_map = {1: 'running', 3: 'paused', 5: 'stopped'}

    # Get VNC port from XML
    xml  = dom.XMLDesc()
    root = ET.fromstring(xml)
    vnc_port = None
    for graphics in root.findall('.//graphics[@type="vnc"]'):
        vnc_port = graphics.get('port')

    result = {
        'name':     dom.name(),
        'state':    state_map.get(info[0], 'unknown'),
        'ram_mb':   info[2] // 1024,
        'vcpus':    info[3],
        'vnc_port': vnc_port,
        'uuid':     dom.UUIDString()
    }

    # If running, get live CPU and RAM usage
    if dom.isActive():
        try:
            stats = dom.memoryStats()
            result['ram_used_mb'] = stats.get(
                'rss', 0) // 1024
        except:
            pass

    conn.close()
    return result


def get_host_stats():
    """Get the physical host machine's resource usage"""
    import psutil
    return {
        'cpu_percent':  psutil.cpu_percent(interval=1),
        'ram_total_gb': round(psutil.virtual_memory().total
                              / (1024**3), 1),
        'ram_used_gb':  round(psutil.virtual_memory().used
                              / (1024**3), 1),
        'ram_percent':  psutil.virtual_memory().percent,
        'disk_total_gb':round(psutil.disk_usage('/').total
                              / (1024**3), 1),
        'disk_used_gb': round(psutil.disk_usage('/').used
                              / (1024**3), 1),
    }


def list_isos():
    """List available ISO files for OS installation"""
    isos = []
    if os.path.exists(ISO_DIR):
        for f in os.listdir(ISO_DIR):
            if f.endswith('.iso') or f.endswith('.img'):
                isos.append({
                    'name': f,
                    'path': os.path.join(ISO_DIR, f),
                    'size_mb': round(
                        os.path.getsize(
                            os.path.join(ISO_DIR, f))
                        / (1024**2), 1)
                })
    return isos
