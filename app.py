from flask import Flask, render_template, request, jsonify, redirect, url_for
import vm_manager
import os

app = Flask(__name__)

# ─── ROUTES (Pages) ────────────────────────────────────────────

@app.route('/')
def index():
    """Main dashboard — shows all VMs"""
    vms        = vm_manager.list_vms()
    host_stats = vm_manager.get_host_stats()
    isos       = vm_manager.list_isos()
    return render_template('index.html',
                           vms=vms,
                           host_stats=host_stats,
                           isos=isos)


@app.route('/vm/<name>')
def vm_detail(name):
    """Detail page for a single VM"""
    vm = vm_manager.get_vm_info(name)
    return render_template('vm_detail.html', vm=vm)


# ─── API ENDPOINTS ─────────────────────────────────────────────

@app.route('/api/vms', methods=['GET'])
def api_list_vms():
    """API: Get all VMs as JSON"""
    return jsonify(vm_manager.list_vms())


@app.route('/api/vm/create', methods=['POST'])
def api_create_vm():
    """API: Create a new VM"""
    data = request.json
    try:
        result = vm_manager.create_vm(
            name     = data['name'],
            ram_mb   = int(data['ram_mb']),
            vcpus    = int(data['vcpus']),
            disk_gb  = int(data['disk_gb']),
            iso_path = data.get('iso_path')
        )
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/vm/<name>/start', methods=['POST'])
def api_start_vm(name):
    """API: Start a VM"""
    try:
        result = vm_manager.start_vm(name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/vm/<name>/stop', methods=['POST'])
def api_stop_vm(name):
    """API: Stop a VM"""
    force = request.json.get('force', False)
    try:
        result = vm_manager.stop_vm(name, force=force)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/vm/<name>/delete', methods=['DELETE'])
def api_delete_vm(name):
    """API: Delete a VM"""
    try:
        result = vm_manager.delete_vm(name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/host/stats', methods=['GET'])
def api_host_stats():
    """API: Get host machine stats"""
    return jsonify(vm_manager.get_host_stats())


if __name__ == '__main__':
    # Run on all interfaces so you can access from browser
    app.run(host='0.0.0.0', port=5000, debug=True)
