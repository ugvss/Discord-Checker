import json
import random
import string
import time
import requests
import sys
import itertools
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)

class FMMVChecker:
    def __init__(self):
        self.load_config()
        self.load_proxies()
        self.api_url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
        
        # Cloud Logic: Session Persistence to avoid "Cold Connection" flags
        self.session = requests.Session()
        
        # Cloud Logic: Infinite Proxy Cycling
        if self.proxies:
            self.proxy_cycle = itertools.cycle(self.proxies)
        else:
            self.proxy_cycle = None
        
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except Exception:
            print(f"{Fore.RED}[!] Error: config.json missing or invalid.")
            sys.exit()

    def load_proxies(self):
        try:
            with open('proxy.txt', 'r') as f:
                lines = f.read().splitlines()
                # Handles user:pass@host:port
                self.proxies = [f"http://{line.strip()}" for line in lines if line.strip()]
            
            if not self.proxies:
                print(f"{Fore.YELLOW}[*] No proxies found in proxy.txt.")
            else:
                print(f"{Fore.CYAN}[*] Loaded {len(self.proxies)} proxies into rotation.")
        except FileNotFoundError:
            self.proxies = []

    def get_proxy(self):
        if not self.proxy_cycle: return None
        return {"http": next(self.proxy_cycle), "https": next(self.proxy_cycle)}

    def send_webhook(self, username):
        # Simplified Webhook as requested
        payload = {
            "embeds": [{
                "title": "Hit Available 🎯",
                "description": f"Username: **{username}**",
                "color": 1752220, # Green
            }]
        }
        try:
            requests.post(self.config['webhook_url'], json=payload, timeout=5)
        except:
            pass

    def check_username(self, username):
        # Human Jitter to prevent "Fake" 429s
        time.sleep(random.uniform(0.3, 0.8))
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/register"
        }
        
        attempts = 0
        while attempts < self.config.get('retry_limit', 5):
            proxy = self.get_proxy()
            try:
                response = self.session.post(
                    self.api_url,
                    json={"username": username},
                    headers=headers,
                    proxies=proxy,
                    timeout=self.config.get('timeout', 7)
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("taken") is False:
                        print(f"{Fore.GREEN}[+] AVAILABLE: {username}")
                        self.send_webhook(username)
                        # Save to local file as backup
                        with open("hits.txt", "a") as f:
                            f.write(f"{username}\n")
                        return True
                    else:
                        print(f"{Fore.RED}[-] TAKEN: {username}")
                        return False
                
                elif response.status_code == 429:
                    # If rate limited, skip this proxy and try next one in cycle immediately
                    attempts += 1
                    continue 
                
                else:
                    attempts += 1
                    break

            except Exception:
                attempts += 1
                continue
        return None

def generate_user(mode):
    chars = string.ascii_lowercase + string.digits + "_."
    if mode == '2': return ''.join(random.choices(chars, k=4))
    if mode == '3': return ''.join(random.choices(string.ascii_lowercase, k=4))
    if mode == '4': return ''.join(random.choices(chars, k=3))
    return None

def main():
    checker = FMMVChecker()
    print(f"\n{Fore.BLUE}╔══════════════════════════════════════════════╗")
    print(f"{Fore.BLUE}║                 FMMV CHECKER                 ║")
    print(f"{Fore.BLUE}║            Made by @fmmv on Discord          ║")
    print(f"{Fore.BLUE}╚══════════════════════════════════════════════╝")
    print(f"{Fore.WHITE}1. Load list.txt")
    print(f"{Fore.WHITE}2. Random 4-character (Mixed)")
    print(f"{Fore.WHITE}3. Random 4-letter")
    print(f"{Fore.WHITE}4. Random 3-character")
    
    choice = input(f"\n{Fore.CYAN}Select Mode: ")
    
    usernames = []
    if choice == '1':
        try:
            with open('list.txt', 'r') as f:
                usernames = f.read().splitlines()
        except:
            print(f"{Fore.RED}[!] list.txt not found."); return
    else:
        # Buffer to fill the thread pool
        usernames = [generate_user(choice) for _ in range(100)]

    # Concurrency control via Threads
    with ThreadPoolExecutor(max_workers=checker.config['threads']) as executor:
        futures = {executor.submit(checker.check_username, u): u for u in usernames}
        
        try:
            while futures:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for f in done:
                    futures.pop(f)
                    if choice != '1':
                        new_u = generate_user(choice)
                        futures[executor.submit(checker.check_username, new_u)] = new_u
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Shutting down safely...")

if __name__ == "__main__":
    main()