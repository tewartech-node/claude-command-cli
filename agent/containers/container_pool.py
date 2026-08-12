"""
Container LLM Pool Manager

Manages multiple containerized LLM instances with load balancing.
"""

import asyncio
import httpx
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ContainerLLMPool:
    """Manages pool of containerized LLM instances"""

    def __init__(self, container_urls: List[str]):
        """
        Initialize container pool

        Args:
            container_urls: List of container URLs
                e.g., ["http://localhost:5000", "http://localhost:5001"]
        """
        self.container_urls = container_urls
        self.current = 0
        self.health_status: Dict[str, bool] = {url: True for url in container_urls}
        self.request_counts: Dict[str, int] = {url: 0 for url in container_urls}

    async def execute(self, prompt: str, model: str = "mistral", **kwargs) -> Optional[Dict]:
        """
        Execute inference with load balancing

        Args:
            prompt: Inference prompt
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            Response from container or None
        """

        # Try containers in round-robin with health awareness
        for _ in range(len(self.container_urls) * 2):
            container_url = self._select_next_container()

            if not self.health_status.get(container_url, True):
                continue

            try:
                result = await self._execute_on_container(container_url, prompt, model, **kwargs)
                self.request_counts[container_url] += 1
                return result
            except Exception as e:
                logger.warning(f"Container {container_url} failed: {e}")
                self.health_status[container_url] = False
                await self._check_health(container_url)

        logger.error("All containers failed")
        return None

    async def execute_parallel(self, prompts: List[str], model: str = "mistral", **kwargs) -> List[Optional[Dict]]:
        """
        Execute multiple prompts in parallel

        Args:
            prompts: List of prompts
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            List of responses
        """

        tasks = [self.execute(prompt, model, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _select_next_container(self) -> str:
        """Select next container using round-robin"""
        self.current = (self.current + 1) % len(self.container_urls)
        return self.container_urls[self.current]

    async def _execute_on_container(self, container_url: str, prompt: str, model: str, **kwargs) -> Dict:
        """Execute on specific container"""

        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "top_k": kwargs.get("top_k", 40),
            }

            if "max_tokens" in kwargs:
                payload["max_tokens"] = kwargs["max_tokens"]

            response = await client.post(
                f"{container_url}/inference",
                json=payload
            )

            if response.status_code == 200:
                self.health_status[container_url] = True
                return response.json()
            else:
                raise Exception(f"Container error: {response.status_code}")

    async def _check_health(self, container_url: str):
        """Check container health"""

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{container_url}/health")
                self.health_status[container_url] = response.status_code == 200
        except Exception:
            self.health_status[container_url] = False

    async def health_check_loop(self, interval: int = 30):
        """Periodically check container health"""

        while True:
            for container_url in self.container_urls:
                await self._check_health(container_url)
            await asyncio.sleep(interval)

    def get_stats(self) -> Dict:
        """Get pool statistics"""

        return {
            "containers": len(self.container_urls),
            "healthy": sum(1 for h in self.health_status.values() if h),
            "request_counts": self.request_counts,
            "health_status": self.health_status,
        }

    def add_container(self, url: str):
        """Add container to pool"""
        if url not in self.container_urls:
            self.container_urls.append(url)
            self.health_status[url] = True
            self.request_counts[url] = 0

    def remove_container(self, url: str):
        """Remove container from pool"""
        if url in self.container_urls:
            self.container_urls.remove(url)
            del self.health_status[url]
            del self.request_counts[url]
