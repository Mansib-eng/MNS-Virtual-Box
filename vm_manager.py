import libvirt
import os
import subprocess
import xml.etree.ElementTree as ET
import json

# Directory to store VM disk images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DISK_DIR = os.path.join(BASE_DIR, "disks")
ISO_DIR  = os.path.join(BASE_DIR, "iso")

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.iso', '.img', '.qcow2'}

# Resource limits
MAX_VCPUS    = os.cpu_count()
MAX_RAM_MB   = int(os.popen("free -m | awk '/Mem:/{print $7}'").read().strip())
MAX_DISK_GB  = int(os.popen("df -BG / | awk 'NR==2{print $4}'").read().strip().replace('G',''))


def validate_vm_params(name, ram_mb, vcpus, disk_gb, iso_path=None):
    """Validate all VM creation parameters — server side"""
    import re

    # Validate name
    if not name:
        raise ValueError("VM name is required")
    if not re.match(r'^[a-zA-Z0-9\-_]+$', name):
        raise ValueError("VM name can only contain letters, numbers, hyphens and underscores")
    if len(name) > 50:
        raise ValueError("VM name must be under 50 characters")

    # Check if VM already exists
    try:
        conn = get_connection()
        conn.lookupByName(name)
        conn.close()
        raise ValueError(f"VM '{name}' already exists")
    except libvirt.libvirtError:
        pass  # Good — VM doesn't exist yet

    # Validate RAM
    if ram_mb < 512:
        raise ValueError("RAM must be at least 512 MB")
    if ram_mb > MAX_RAM_MB:
        raise ValueError(f"RAM cannot exceed available host RAM ({MAX_RAM_MB} MB)")

    # Validate vCPUs
    if vcpus < 1:
        raise ValueError("vCPUs must be at least 1")
    if vcpus > MAX_VCPUS:
        raise ValueError(f"vCPUs cannot exceed host CPU count ({MAX_VCPUS})")

    # Validate disk
    if disk_gb < 5:
        raise ValueError("Disk must be at least 5 GB")
    if disk_gb > MAX_DISK_GB:
        raise ValueError(f"Disk cannot exceed available storage ({MAX_DISK_GB} GB)")

    # Validate image path
    if iso_path:
        # Must be inside ISO_DIR (prevent path traversal)
        real_iso  = os.path.realpath(iso_path)
        real_dir  = os.path.realpath(ISO_DIR)
        if not real_iso.startswith(real_dir):
            raise ValueError("Image must be inside the approved image directory")

        # Must exist
        if not os.path.exists(iso_path):
            raise ValueError(f"Image file not found: {iso_path}")

        # Must have allowed extension
        ext = os.path.splitext(iso_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Image type '{ext}' not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}")

    return True

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
    """Create a new Virtual Machine with proper validation and image handling"""

    # Step 1: Validate all parameters first
    validate_vm_params(name, ram_mb, vcpus, disk_gb, iso_path)

    disk_path = os.path.join(DISK_DIR, f"{name}.qcow2")

    # Step 2: Handle image types correctly
    if iso_path:
        ext = os.path.splitext(iso_path)[1].lower()

        if ext in ('.img', '.qcow2'):
            # Pre-installed disk image — convert to qcow2 properly
            print(f"Converting {ext} image to qcow2...")
            subprocess.run([
                'qemu-img', 'convert',
                '-p',           # Show progress
                '-O', 'qcow2',  # Output format
                iso_path,       # Input image
                disk_path       # Output disk
            ], check=True)

            # Resize to requested size if larger than image
            subprocess.run([
                'qemu-img', 'resize',
                disk_path,
                f'{disk_gb}G'
            ], check=True)

            # Build virt-install command for pre-installed image
            cmd = [
                'virt-install',
                '--connect',      'qemu:///system',
                '--name',         name,
                '--ram',          str(ram_mb),
                '--vcpus',        str(vcpus),
                '--disk',         f'path={disk_path},format=qcow2',
                '--os-variant',   'generic',
                '--network',      'network=default',
                '--graphics',     'vnc,listen=127.0.0.1',
                '--noautoconsole',
                '--import',
                '--boot',         'hd',
            ]

        else:
            # .iso installer — create blank disk and boot from ISO
            subprocess.run([
                'qemu-img', 'create',
                '-f', 'qcow2',
                disk_path,
                f'{disk_gb}G'
            ], check=True)

            # Detect OS variant from filename
            os_variant = detect_os_variant(iso_path)

            cmd = [
                'virt-install',
                '--connect',      'qemu:///system',
                '--name',         name,
                '--ram',          str(ram_mb),
                '--vcpus',        str(vcpus),
                '--disk',         f'path={disk_path},format=qcow2',
                '--os-variant',   os_variant,
                '--network',      'network=default',
                '--graphics',     'vnc,listen=127.0.0.1',
                '--noautoconsole',
                '--cdrom',        iso_path,
            ]
    else:
        raise ValueError("Please select an image file (.iso, .img, or .qcow2)")

    # Step 3: Run virt-install
    subprocess.run(cmd, check=True)

    return {
        'status':    'created',
        'name':      name,
        'disk':      disk_path,
        'ram_mb':    ram_mb,
        'vcpus':     vcpus,
        'disk_gb':   disk_gb,
    }


def detect_os_variant(iso_path):
    """Detect OS variant from ISO filename for virt-install"""
    name = os.path.basename(iso_path).lower()

    if 'ubuntu-24' in name: return 'ubuntu24.04'
    if 'ubuntu-22' in name: return 'ubuntu22.04'
    if 'ubuntu-20' in name: return 'ubuntu20.04'
    if 'ubuntu'    in name: return 'ubuntu22.04'
    if 'debian-12' in name: return 'debian12'
    if 'debian'    in name: return 'debian12'
    if 'fedora'    in name: return 'fedora38'
    if 'centos'    in name: return 'centos-stream9'
    if 'alpine'    in name: return 'alpinelinux3.17'
    if 'cirros'    in name: return 'generic'

    return 'generic'  # Safe fallback
  

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

    try:
        dom = conn.lookupByName(name)
    except libvirt.libvirtError:
        conn.close()
        raise ValueError(f"VM '{name}' not found")

    info = dom.info()
    state_map = {
        0: 'no state',
        1: 'running',
        2: 'blocked',
        3: 'paused',
        4: 'shutting down',
        5: 'stopped',
        6: 'crashed'
    }

    # Parse XML for real values
    xml  = dom.XMLDesc()
    root = ET.fromstring(xml)

    # Get VNC port correctly
    vnc_port    = None
    vnc_display = None
    for graphics in root.findall('.//graphics[@type="vnc"]'):
        raw_port = graphics.get('port')
        if raw_port and raw_port != '-1':
            vnc_port    = int(raw_port)
            # Display number = port - 5900
            vnc_display = vnc_port - 5900

    # Get real machine type
    machine_type = 'pc'
    for os_el in root.findall('.//type'):
        machine_type = os_el.get('machine', 'pc')

    # Get real architecture
    arch = 'x86_64'
    for os_el in root.findall('.//type'):
        arch = os_el.get('arch', 'x86_64')

    # Get disk path
    disk_path = None
    for disk in root.findall('.//disk[@device="disk"]/source'):
        disk_path = disk.get('file')

    # Get disk size — use virsh domblkinfo (works even while VM is running)
    disk_size_gb = None
    if disk_path:
        try:
            result2 = subprocess.run(
                ['virsh', '--connect', 'qemu:///system',
                 'domblkinfo', name, disk_path, '--human'],
                capture_output=True, text=True
            )
            for line in result2.stdout.splitlines():
                if 'Capacity' in line:
                    # Line looks like: "Capacity:       10.000 GiB"
                    parts = line.split()
                    if len(parts) >= 2:
                        val = float(parts[1])
                        unit = parts[2] if len(parts) > 2 else 'GiB'
                        if 'GiB' in unit or 'GB' in unit:
                            disk_size_gb = round(val, 1)
                        elif 'MiB' in unit or 'MB' in unit:
                            disk_size_gb = round(val / 1024, 1)
                    break
        except Exception:
            pass

    # Get network interface
    mac_address = None
    for mac in root.findall('.//interface[@type="network"]/mac'):
        mac_address = mac.get('address')

    result = {
        'name':         dom.name(),
        'state':        state_map.get(info[0], 'unknown'),
        'ram_mb':       info[2] // 1024,
        'vcpus':        info[3],
        'uuid':         dom.UUIDString(),
        'vnc_port':     vnc_port,
        'vnc_display':  vnc_display,
        # Correct VNC command using double colon for exact port
        'vnc_cmd':      f'vncviewer 127.0.0.1::{vnc_port}' if vnc_port else None,
        'machine_type': machine_type,
        'arch':         arch,
        'disk_path':    disk_path,
        'disk_size_gb': disk_size_gb,
        'mac_address':  mac_address,
    }

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
    """List available ISO/IMG files with clean display names"""

    # Map filename keywords to clean display names + emoji
    NAME_MAP = [
        ('ubuntu-24',  '🟣 Ubuntu Server 24.04 LTS'),
        ('ubuntu-22',  '🟣 Ubuntu Server 22.04 LTS'),
        ('ubuntu-20',  '🟣 Ubuntu Server 20.04 LTS'),
        ('ubuntu',     '🟣 Ubuntu Server'),
        ('debian-12',  '🔴 Debian 12 (Bookworm)'),
        ('debian',     '🔴 Debian Linux'),
        ('fedora',     '🔵 Fedora Linux'),
        ('centos',     '🟢 CentOS Stream'),
        ('alpine',     '🔷 Alpine Linux'),
        ('cirros',     '🟠 CirrOS — Test Image'),
        ('windows',    '🪟 Windows'),
    ]

    isos = []
    if os.path.exists(ISO_DIR):
        for f in os.listdir(ISO_DIR):
            ext = os.path.splitext(f)[1].lower()
            if ext not in ('.iso', '.img', '.qcow2'):
                continue

            full_path = os.path.join(ISO_DIR, f)
            size_mb   = round(os.path.getsize(full_path) / (1024**2), 1)
            fname     = f.lower()

            # Find a clean display name
            display_name = None
            for keyword, name in NAME_MAP:
                if keyword in fname:
                    display_name = name
                    break

            # Fallback: clean up the raw filename
            if not display_name:
                display_name = f.replace('-', ' ').replace('_', ' ')
                display_name = os.path.splitext(display_name)[0]
                display_name = display_name.title()

            isos.append({
                'name':         f,              # raw filename (used internally)
                'display_name': display_name,   # clean name (shown in UI)
                'path':         full_path,
                'size_mb':      size_mb,
                'type':         ext.upper().replace('.', ''),
            })

    # Sort: ISOs first, then by display name
    isos.sort(key=lambda x: (x['type'] != 'ISO', x['display_name']))
    return isos

def reboot_vm(name):
    """Reboot a running VM"""
    conn = get_connection()
    try:
        dom = conn.lookupByName(name)
        if not dom.isActive():
            raise ValueError(f"VM '{name}' is not running")
        dom.reboot()
        conn.close()
        return {'status': 'rebooting', 'name': name}
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def pause_vm(name):
    """Pause (suspend) a running VM"""
    conn = get_connection()
    try:
        dom = conn.lookupByName(name)
        if not dom.isActive():
            raise ValueError(f"VM '{name}' is not running")
        dom.suspend()
        conn.close()
        return {'status': 'paused', 'name': name}
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def resume_vm(name):
    """Resume a paused VM"""
    conn = get_connection()
    try:
        dom = conn.lookupByName(name)
        dom.resume()
        conn.close()
        return {'status': 'resumed', 'name': name}
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def get_guest_ip(name):
    """Try to get guest IP address from libvirt DHCP leases"""
    conn = get_connection()
    try:
        dom = conn.lookupByName(name)
        if not dom.isActive():
            conn.close()
            return None

        # Method 1: Try libvirt guest agent
        try:
            ifaces = dom.interfaceAddresses(
                libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)
            for iface, data in ifaces.items():
                if iface == 'lo':
                    continue
                for addr in data.get('addrs', []):
                    if addr['type'] == 0:  # IPv4
                        conn.close()
                        return addr['addr']
        except Exception:
            pass

        # Method 2: Try DHCP leases via virsh
        xml  = dom.XMLDesc()
        root = ET.fromstring(xml)
        mac  = None
        for m in root.findall('.//interface[@type="network"]/mac'):
            mac = m.get('address')

        if mac:
            try:
                result = subprocess.run(
                    ['virsh', '--connect', 'qemu:///system',
                     'net-dhcp-leases', 'default'],
                    capture_output=True, text=True
                )
                for line in result.stdout.splitlines():
                    if mac.lower() in line.lower():
                        parts = line.split()
                        for part in parts:
                            if '.' in part and '/' in part:
                                conn.close()
                                return part.split('/')[0]
            except Exception:
                pass

        conn.close()
        return None
    except Exception:
        conn.close()
        return None


def create_snapshot(name, snapshot_name=None):
    """Create a snapshot of a VM"""
    import datetime
    conn = get_connection()
    try:
        dom = conn.lookupByName(name)

        if not snapshot_name:
            snapshot_name = f"snap-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Build snapshot XML
        snap_xml = f"""
        <domainsnapshot>
            <name>{snapshot_name}</name>
            <description>Snapshot of {name} at {datetime.datetime.now()}</description>
        </domainsnapshot>
        """
        dom.snapshotCreateXML(snap_xml, 0)
        conn.close()
        return {'status': 'created', 'snapshot': snapshot_name, 'vm': name}
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def list_snapshots(name):
    """List all snapshots of a VM"""
    conn = get_connection()
    try:
        dom  = conn.lookupByName(name)
        snaps = dom.listAllSnapshots()
        result = []
        for snap in snaps:
            result.append({
                'name':   snap.getName(),
                'current': snap.isCurrent(),
            })
        conn.close()
        return result
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def restore_snapshot(name, snapshot_name):
    """Restore a VM to a snapshot"""
    conn = get_connection()
    try:
        dom  = conn.lookupByName(name)
        snap = dom.snapshotLookupByName(snapshot_name)
        dom.revertToSnapshot(snap)
        conn.close()
        return {'status': 'restored', 'snapshot': snapshot_name, 'vm': name}
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def delete_snapshot(name, snapshot_name):
    """Delete a snapshot"""
    conn = get_connection()
    try:
        dom  = conn.lookupByName(name)
        snap = dom.snapshotLookupByName(snapshot_name)
        snap.delete()
        conn.close()
        return {'status': 'deleted', 'snapshot': snapshot_name}
    except libvirt.libvirtError as e:
        conn.close()
        raise ValueError(str(e))


def get_dynamic_limits():
    """Get real-time available resource limits from host"""
    import psutil
    cpu_total    = psutil.cpu_count()
    ram          = psutil.virtual_memory()
    disk         = psutil.disk_usage(DISK_DIR)

    # Count already allocated resources
    conn = get_connection()
    allocated_ram  = 0
    allocated_cpus = 0
    try:
        for dom in conn.listAllDomains():
            info           = dom.info()
            allocated_ram  += info[2] // 1024   # KB to MB
            allocated_cpus += info[3]
    except Exception:
        pass
    conn.close()

    return {
        'cpu': {
            'total':     cpu_total,
            'allocated': allocated_cpus,
            'available': max(0, cpu_total - allocated_cpus),
        },
        'ram': {
            'total_mb':     ram.total // (1024**2),
            'available_mb': ram.available // (1024**2),
            'allocated_mb': allocated_ram,
        },
        'disk': {
            'total_gb':     disk.total // (1024**3),
            'available_gb': disk.free  // (1024**3),
        }
    }


def list_images():
    """List all available images with metadata"""
    images = []
    if os.path.exists(ISO_DIR):
        for f in os.listdir(ISO_DIR):
            ext = os.path.splitext(f)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                full_path = os.path.join(ISO_DIR, f)
                size_mb   = round(os.path.getsize(full_path) / (1024**2), 1)

                # Determine image type label
                if ext == '.iso':
                    img_type = 'Installer ISO'
                elif ext == '.qcow2':
                    img_type = 'QCOW2 Disk'
                else:
                    img_type = 'Disk Image'

                images.append({
                    'name':     f,
                    'path':     full_path,
                    'size_mb':  size_mb,
                    'type':     img_type,
                    'ext':      ext,
                })
    return images
