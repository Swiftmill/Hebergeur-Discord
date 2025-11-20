import asyncio
import os
import signal
from pathlib import Path
from typing import Dict, Optional

from .config import LOGS_DIR


class BotManager:
    def __init__(self):
        self.processes: Dict[int, asyncio.subprocess.Process] = {}

    async def start_bot(self, bot_id: int, bot_path: Path, language: str, entrypoint: str, token: str) -> int:
        if bot_id in self.processes and self.processes[bot_id].returncode is None:
            return self.processes[bot_id].pid

        log_file = LOGS_DIR / f"{bot_id}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        stdout = await asyncio.to_thread(open, log_file, "a")
        stderr = stdout

        env = os.environ.copy()
        env["DISCORD_TOKEN"] = token
        cmd = []
        if language.lower() == "python":
            cmd = ["python", entrypoint]
        else:
            cmd = ["node", entrypoint]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=bot_path,
            stdout=stdout,
            stderr=stderr,
            env=env,
        )
        self.processes[bot_id] = process
        return process.pid

    async def stop_bot(self, bot_id: int) -> bool:
        process = self.processes.get(bot_id)
        if process and process.returncode is None:
            process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
            except asyncio.TimeoutError:
                process.kill()
            return True
        return False

    async def restart_bot(self, bot_id: int, bot_path: Path, language: str, entrypoint: str, token: str) -> Optional[int]:
        await self.stop_bot(bot_id)
        return await self.start_bot(bot_id, bot_path, language, entrypoint, token)

    def get_status(self, bot_id: int) -> str:
        process = self.processes.get(bot_id)
        if process and process.returncode is None:
            return "running"
        return "stopped"


bot_manager = BotManager()
