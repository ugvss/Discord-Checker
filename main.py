import json
import random
import string
import asyncio
import aiohttp
import itertools
from colorama import Fore, Style, init
import sys

init(autoreset=True)

class FMMVCheckerAsync:
    def __init__(self):
        self.load_config()
        self.load_proxies()
        self.api_url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"

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
                self.proxies = [line.strip() for line in lines if line.strip()]
            
            if not self.proxies:
                print(f"{Fore.YELLOW}[*] No proxies found in proxy.txt.")
            else:
                print(f"{Fore.GREEN}[*] Loaded {len(self.proxies)} proxies into rotation.")
        except FileNotFoundError:
            self.proxies = []

    def get_proxy(self):
        if not self.proxy_cycle:
            return None
        proxy = next(self.proxy_cycle)
        return f"http://{proxy}" if proxy else None

    async def send_webhook(self, username):
        payload = {
            "embeds": [{
                "title": "Available",
                "description": f"`{username}`",
                "color": 0
            }]
        }
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.config['webhook_url'], json=payload, timeout=5)
        except:
            pass

    async def check_username(self, username, session):
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
                async with session.post(
                    self.api_url,
                    json={"username": username},
                    headers=headers,
                    proxy=proxy,
                    timeout=self.config.get('timeout', 7)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data.get("taken"):
                            print(f"{Fore.GREEN}[+] AVAILABLE: {username}")
                            await self.send_webhook(username)
                            with open("hits.txt", "a") as f:
                                f.write(f"{username}\n")
                            return True
                        else:
                            print(f"{Fore.RED}[-] TAKEN: {username}")
                            return False
                    elif response.status == 429:
                        attempts += 1
                        continue
                    else:
                        attempts += 1
                        continue
            except Exception:
                attempts += 1
                continue
        return None

async def generate_user(mode):
    chars = string.ascii_lowercase + string.digits + "_."
    if mode == '2': return ''.join(random.choices(chars, k=4))
    if mode == '3': return ''.join(random.choices(string.ascii_lowercase, k=4))
    if mode == '4': return ''.join(random.choices(chars, k=3))
    return None

async def main():
    checker = FMMVCheckerAsync()
    print(f"\n{Fore.WHITE}╔══════════════════════════════════════════════╗")
    print(f"{Fore.WHITE}║                 FMMV CHECKER                 ║")
    print(f"{Fore.WHITE}║            Made by @fmmv on Discord          ║")
    print(f"{Fore.WHITE}╚══════════════════════════════════════════════╝")
    print(f"{Fore.WHITE}1. list.txt")
    print(f"{Fore.WHITE}2. Random 4C")
    print(f"{Fore.WHITE}3. Random 4L")
    print(f"{Fore.WHITE}4. Random 3C")
    
    choice = input(f"\n{Fore.GREEN}Select Mode: ")
    
    usernames = []
    if choice == '1':
        try:
            with open('list.txt', 'r') as f:
                usernames = f.read().splitlines()
        except:
            print(f"{Fore.RED}[!] list.txt not found.")
            return
    else:
        usernames = [await generate_user(choice) for _ in range(100)]

    async with aiohttp.ClientSession() as session:
        tasks = {asyncio.create_task(checker.check_username(u, session)): u for u in usernames}

        try:
            while tasks:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for f in done:
                    tasks.pop(f)
                    if choice != '1':
                        new_u = await generate_user(choice)
                        tasks[asyncio.create_task(checker.check_username(new_u, session))] = new_u
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Shutting down safely...")

if __name__ == "__main__":
    asyncio.run(main())
