import os
import asyncio

async def main():
    token = os.getenv("DISCORD_TOKEN", "demo-token")
    while True:
        print(f"Example bot alive with token: {token}")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
