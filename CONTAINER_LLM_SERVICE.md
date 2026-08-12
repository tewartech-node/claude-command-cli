# Containerized Tiny LLM Service

Run a lightweight LLM in Docker/Podman that your agent framework can communicate with.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Agent Framework (Your Repo)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FreeAgentPool → Agent requests → REST/gRPC                │
│                                                              │
│              ↓ ↓ ↓ ↓ ↓ ↓ ↓                                   │
│              Network (TCP)                                   │
│              ↓ ↓ ↓ ↓ ↓ ↓ ↓                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│        Docker Container: Tiny LLM Service                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Server (FastAPI or Flask)                         │ │
│  │  ├─ /inference    (REST)                              │ │
│  │  ├─ /health       (Health check)                      │ │
│  │  └─ /stats        (Metrics)                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tiny LLM (Ollama, TinyLLaMA, or Mistral)              │ │
│  │  Memory: 1-4GB   CPU: 1-2 cores                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Model Storage (/models)                               │ │
│  │  • Mistral-7B (3.5GB)                                  │ │
│  │  • TinyLLaMA-1.1B (600MB)                              │ │
│  │  • Phi-2 (1.5GB)                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Container Options

### Option 1: Minimal (Recommended)
**Size**: 500MB-1GB (including model)
**Models**: TinyLLaMA-1.1B, Phi-2
**Memory**: 1-2GB
**CPU**: 1-2 cores
**Inference Speed**: 5-10 tokens/sec

### Option 2: Standard
**Size**: 2-4GB (including model)
**Models**: Mistral-7B, Dolphin-2.6
**Memory**: 2-4GB
**CPU**: 2-4 cores
**Inference Speed**: 10-20 tokens/sec

### Option 3: Performance
**Size**: 8-16GB (including model)
**Models**: Mistral-Medium, Yi-34B
**Memory**: 8-16GB
**CPU**: 4-8 cores
**Inference Speed**: 20-50 tokens/sec

## Quick Start (3 Steps)

### 1. Build Container

```bash
# Clone model from Ollama (7B Mistral)
docker run -d \
  --name tiny-llm \
  -p 5000:5000 \
  -v llm_models:/models \
  -e MODEL_NAME="mistral:latest" \
  -e API_PORT="5000" \
  ghcr.io/jmorganca/ollama

# Or use pre-built lightweight image
docker pull ollama/ollama:latest
```

### 2. Test Container

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "prompt": "What is 2+2?",
    "stream": false
  }'
```

### 3. Integrate with Agent Framework

```python
from agent.agents import FreeAgentPool, OllamaAgent

# Add containerized LLM as agent
pool = FreeAgentPool()
container_agent = OllamaAgent(
    model="mistral:latest",
    base_url="http://localhost:5000"
)
pool.register_custom_agent("container-llm", container_agent)

# Use it
result = await pool.execute_with_fallback(
    "Analyze this data",
    task_type="analysis"
)
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

```yaml
version: '3.8'

services:
  tiny-llm:
    image: ollama/ollama:latest
    container_name: tiny-llm-service
    ports:
      - "5000:11434"
    volumes:
      - llm_models:/root/.ollama/models
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  api-gateway:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: llm-api-gateway
    ports:
      - "5001:5001"
    environment:
      - OLLAMA_HOST=http://tiny-llm:11434
      - API_PORT=5001
    depends_on:
      tiny-llm:
        condition: service_healthy
    restart: unless-stopped

volumes:
  llm_models:
    driver: local
```

### Method 2: Kubernetes (Production)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tiny-llm
  labels:
    app: tiny-llm
spec:
  containers:
  - name: ollama
    image: ollama/ollama:latest
    ports:
    - containerPort: 11434
    resources:
      requests:
        memory: "2Gi"
        cpu: "1"
      limits:
        memory: "4Gi"
        cpu: "2"
    volumeMounts:
    - name: models
      mountPath: /root/.ollama/models
    livenessProbe:
      httpGet:
        path: /api/tags
        port: 11434
      initialDelaySeconds: 30
      periodSeconds: 10
  volumes:
  - name: models
    emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: tiny-llm-service
spec:
  selector:
    app: tiny-llm
  ports:
  - protocol: TCP
    port: 11434
    targetPort: 11434
  type: ClusterIP
```

### Method 3: Podman (Rootless)

```bash
# Create pod
podman pod create --name tiny-llm-pod -p 5000:11434

# Run container in pod
podman run -d \
  --name tiny-llm \
  --pod tiny-llm-pod \
  -v llm_models:/root/.ollama/models \
  ollama/ollama:latest

# Start container
podman start tiny-llm
```

## Lightweight Model Options

### TinyLLaMA (Recommended for containers)
```
Model: TinyLLaMA-1.1B
Size: 600MB
Memory: 1GB
Speed: 5-10 tok/s
Quality: Good for simple tasks
```

**Pull**: `ollama pull tinyllama`

### Mistral-7B
```
Model: Mistral-7B
Size: 3.5GB
Memory: 4GB
Speed: 10-20 tok/s
Quality: Great for complex tasks
```

**Pull**: `ollama pull mistral`

### Phi-2
```
Model: Phi-2
Size: 1.5GB
Memory: 2GB
Speed: 8-15 tok/s
Quality: Excellent reasoning
```

**Pull**: `ollama pull phi`

### Neural Chat
```
Model: Neural-Chat-7B
Size: 3.5GB
Memory: 4GB
Speed: 12-18 tok/s
Quality: Great for conversation
```

**Pull**: `ollama pull neural-chat`

## API Endpoints

### REST API (Ollama Compatible)

**Generate Text**
```http
POST /api/generate
Content-Type: application/json

{
  "model": "mistral",
  "prompt": "Your prompt here",
  "stream": false,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40
}

Response:
{
  "model": "mistral",
  "created_at": "2026-08-12T10:30:00Z",
  "response": "The answer is...",
  "done": true,
  "context": [...],
  "total_duration": 234567890,
  "load_duration": 123456789,
  "prompt_eval_count": 25,
  "prompt_eval_duration": 34567890,
  "eval_count": 100,
  "eval_duration": 76543210
}
```

**List Models**
```http
GET /api/tags

Response:
{
  "models": [
    {
      "name": "mistral:latest",
      "modified_at": "2026-08-12T10:00:00Z",
      "size": 3853587808,
      "digest": "61857..."
    }
  ]
}
```

**Health Check**
```http
GET /api/health

Response: 200 OK
```

## Integration with Agent Framework

### Option A: Direct Integration

```python
from agent.agents import FreeAgentPool, OllamaAgent

class ContainerLLMAgent(OllamaAgent):
    """Agent wrapper for containerized LLM"""
    
    def __init__(self, container_url="http://localhost:5000"):
        super().__init__(
            model="mistral:latest",
            base_url=container_url
        )
    
    async def execute(self, prompt: str, **kwargs):
        # Add retry logic for container restarts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await super().execute(prompt, **kwargs)
            except ConnectionError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

# Use in agent pool
pool = FreeAgentPool()
container_agent = ContainerLLMAgent()
pool.register_custom_agent("container", container_agent)
```

### Option B: Load Balancing

```python
class ContainerLLMPool:
    """Multiple containers with load balancing"""
    
    def __init__(self, container_urls=None):
        self.containers = container_urls or [
            "http://localhost:5000",
            "http://localhost:5001",
            "http://localhost:5002",
        ]
        self.agents = [
            OllamaAgent(base_url=url) for url in self.containers
        ]
        self.current = 0
    
    async def execute(self, prompt: str, **kwargs):
        """Round-robin between containers"""
        for _ in range(len(self.agents)):
            agent = self.agents[self.current]
            self.current = (self.current + 1) % len(self.agents)
            
            try:
                result = await agent.execute(prompt, **kwargs)
                if result.success:
                    return result
            except Exception:
                continue
        
        raise Exception("All containers failed")
```

### Option C: Auto-Scaling

```python
class AutoScalingContainerPool:
    """Automatically scales containers based on load"""
    
    def __init__(self, docker_client, min_containers=1, max_containers=5):
        self.docker = docker_client
        self.min_containers = min_containers
        self.max_containers = max_containers
        self.containers = []
        self.queue_depth = 0
    
    async def execute(self, prompt: str, **kwargs):
        # Track queue depth
        self.queue_depth += 1
        
        # Scale up if needed
        if self.queue_depth > len(self.containers) * 2:
            await self._scale_up()
        
        # Execute on least-loaded container
        result = await self._execute_on_least_loaded(prompt, **kwargs)
        
        # Scale down if idle
        self.queue_depth -= 1
        if self.queue_depth == 0:
            await self._scale_down()
        
        return result
    
    async def _scale_up(self):
        """Add new container"""
        if len(self.containers) < self.max_containers:
            # Start new container via Docker API
            container = self.docker.containers.run(
                "ollama/ollama",
                detach=True,
                ports={'11434/tcp': None}
            )
            self.containers.append(container)
    
    async def _scale_down(self):
        """Remove idle container"""
        if len(self.containers) > self.min_containers:
            container = self.containers.pop()
            container.stop()
            container.remove()
```

## Monitoring & Observability

### Container Logs
```bash
# View logs
docker logs -f tiny-llm

# Watch metrics
docker stats tiny-llm
```

### Prometheus Metrics

```yaml
# Add to container
environment:
  - OLLAMA_METRICS=true
```

Access metrics at: `http://localhost:5000/metrics`

### Grafana Dashboard

```json
{
  "dashboard": {
    "panels": [
      {
        "title": "Inference Latency",
        "targets": [
          {"expr": "ollama_inference_duration_seconds"}
        ]
      },
      {
        "title": "Model Load Time",
        "targets": [
          {"expr": "ollama_load_duration_seconds"}
        ]
      },
      {
        "title": "Tokens/Second",
        "targets": [
          {"expr": "rate(ollama_eval_count[1m])"}
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {"expr": "ollama_memory_usage_bytes"}
        ]
      }
    ]
  }
}
```

## Resource Requirements

| Model | Container Size | Memory | CPU | Speed |
|-------|-----------------|--------|-----|-------|
| TinyLLaMA-1.1B | 700MB | 1GB | 1 | 5-10 tok/s |
| Phi-2 | 1.8GB | 2GB | 1 | 8-15 tok/s |
| Mistral-7B | 4GB | 3GB | 2 | 10-20 tok/s |
| Dolphin-2.6-7B | 4GB | 3GB | 2 | 12-18 tok/s |
| Mistral-Medium | 8GB | 6GB | 4 | 15-25 tok/s |

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs tiny-llm

# Verify GPU (if using)
docker run --rm --gpus all nvidia/cuda:11.8.0-runtime nvidia-smi

# Check disk space
df -h /var/lib/docker
```

### Slow Inference
```bash
# Monitor metrics
docker stats tiny-llm

# Reduce model size or CPU load
# or allocate more resources

# Enable GPU acceleration
docker run --gpus all ollama/ollama
```

### Out of Memory
```bash
# Reduce model size
# or increase container memory

# Swap smaller model
ollama pull tinyllama
```

## Production Deployment Checklist

- [ ] Choose lightweight model (TinyLLaMA or Phi-2)
- [ ] Set resource limits (CPU, memory)
- [ ] Enable health checks
- [ ] Configure restart policy
- [ ] Set up monitoring/logging
- [ ] Configure auto-scaling if needed
- [ ] Test failover/recovery
- [ ] Document configuration
- [ ] Set up alerts
- [ ] Plan for updates

## Cost Analysis

### Local Hosting (Your Infrastructure)
- **Infrastructure**: $0 (uses existing hardware)
- **Electricity**: ~$2-5/month (2-4GB RAM + CPU)
- **Maintenance**: ~2 hours/month
- **Total**: $0-5/month + maintenance

### Cloud Hosting (Optional)
- **AWS t3.medium**: $30/month + $0.10/GB storage
- **Google Cloud e2-medium**: $25/month + storage
- **DigitalOcean**: $12/month (smallest option)

### Comparison to Paid APIs
- **OpenAI API**: $0.015/1K tokens
- **Anthropic Claude**: $0.01-0.1/1K tokens
- **Cohere**: $0.015/1K tokens
- **Local Container**: $0 (unlimited tokens)

## Next Steps

1. **Setup**: `docker-compose up -d`
2. **Verify**: `curl http://localhost:5000/api/tags`
3. **Integrate**: Add to FreeAgentPool
4. **Test**: Run sample inference
5. **Monitor**: Check logs and metrics
6. **Scale**: Add more containers if needed

---

**Status**: Ready for deployment
**Tested Models**: TinyLLaMA, Phi-2, Mistral
**Container Size**: 500MB - 4GB
**Memory Usage**: 1GB - 4GB
**Startup Time**: 10-30 seconds
