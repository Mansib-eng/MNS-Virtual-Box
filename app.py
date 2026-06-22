from flask import Flask, render_template, request, jsonify, redirect, url_for
import vm_manager
import os
import time
import json

app = Flask(__name__)

# ─── ROUTES (Pages) ────────────────────────────────────────────

@app.route('/')
def index():
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
    data = request.json

    # Check all required fields exist
    required = ['name', 'ram_mb', 'vcpus', 'disk_gb']
    for field in required:
        if field not in data:
            return jsonify({'success': False,
                           'error': f'Missing field: {field}'}), 400
    try:
        result = vm_manager.create_vm(
            name     = str(data['name']).strip(),
            ram_mb   = int(data['ram_mb']),
            vcpus    = int(data['vcpus']),
            disk_gb  = int(data['disk_gb']),
            iso_path = data.get('iso_path') or None
        )
        return jsonify({'success': True, 'result': result})
    except ValueError as e:
        # Validation errors — user's fault
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        # System errors
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vm/<name>')
def api_vm_detail(name):
    """Return 404 if VM not found"""
    try:
        vm = vm_manager.get_vm_info(name)
        return jsonify(vm)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

# ── REBOOT ──
@app.route('/api/vm/<name>/reboot', methods=['POST'])
def api_reboot_vm(name):
    try:
        result = vm_manager.reboot_vm(name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ── PAUSE ──
@app.route('/api/vm/<name>/pause', methods=['POST'])
def api_pause_vm(name):
    try:
        result = vm_manager.pause_vm(name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ── RESUME ──
@app.route('/api/vm/<name>/resume', methods=['POST'])
def api_resume_vm(name):
    try:
        result = vm_manager.resume_vm(name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ── GUEST IP ──
@app.route('/api/vm/<name>/ip', methods=['GET'])
def api_guest_ip(name):
    try:
        ip = vm_manager.get_guest_ip(name)
        return jsonify({'success': True, 'ip': ip})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ── SNAPSHOTS ──
@app.route('/api/vm/<name>/snapshots', methods=['GET'])
def api_list_snapshots(name):
    try:
        snaps = vm_manager.list_snapshots(name)
        return jsonify({'success': True, 'snapshots': snaps})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/vm/<name>/snapshot/create', methods=['POST'])
def api_create_snapshot(name):
    data          = request.json or {}
    snapshot_name = data.get('snapshot_name', None)
    try:
        result = vm_manager.create_snapshot(name, snapshot_name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/vm/<name>/snapshot/<snap_name>/restore', methods=['POST'])
def api_restore_snapshot(name, snap_name):
    try:
        result = vm_manager.restore_snapshot(name, snap_name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/vm/<name>/snapshot/<snap_name>/delete', methods=['DELETE'])
def api_delete_snapshot(name, snap_name):
    try:
        result = vm_manager.delete_snapshot(name, snap_name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ── DYNAMIC LIMITS ──
@app.route('/api/host/limits', methods=['GET'])
def api_host_limits():
    try:
        limits = vm_manager.get_dynamic_limits()
        return jsonify({'success': True, 'limits': limits})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ── IMAGE LIST ──
@app.route('/api/images', methods=['GET'])
def api_list_images():
    try:
        images = vm_manager.list_images()
        return jsonify({'success': True, 'images': images})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ── SERVER-SENT EVENTS ──
@app.route('/api/events')
def sse_stream():
    """
    Real-time event stream using Server-Sent Events.
    Browser connects once, server pushes updates whenever VM state changes.
    """
    def generate():
        last_state = None
        while True:
            try:
                # Get current VM states + host stats
                vms        = vm_manager.list_vms()
                host_stats = vm_manager.get_host_stats()

                current_state = {
                    'vms':        vms,
                    'host_stats': host_stats,
                    'running':    sum(1 for v in vms if v['state'] == 'running'),
                    'total':      len(vms),
                }

                # Only push if something changed
                state_sig = json.dumps(
                    [(v['name'], v['state']) for v in vms]
                )

                if state_sig != last_state:
                    last_state = state_sig
                    payload    = json.dumps(current_state)
                    yield f"data: {payload}\n\n"

                # Send heartbeat every 5 seconds to keep connection alive
                else:
                    yield f": heartbeat\n\n"

                time.sleep(3)  # Check every 3 seconds

            except GeneratorExit:
                break
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(5)

    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':   'no-cache',
            'X-Accel-Buffering': 'no',   # Disable nginx buffering
            'Connection':      'keep-alive',
        }
    )


if __name__ == '__main__':
    app.run(
        host=os.getenv('APP_HOST', '0.0.0.0'),
        port=int(os.getenv('APP_PORT', '5000')),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
