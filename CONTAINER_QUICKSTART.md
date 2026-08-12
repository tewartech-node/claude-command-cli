# Container LLM Service - Quick Start

Get your containerized LLM running in 5 minutes.

## Prerequisites

- Docker or Podman installed
- 4GB+ available memory
- 10GB+ available disk space (for model downloads)

## Option 1: Docker Compose (Recommended)

### 1. Start Containers

```bash
# Navigate to repo
cd /home/user/claude-command-cli

# Start Ollama + API Gateway
docker-compose up -d

# Verify startup
docker-compose ps
```

**Expected output:**
```
CONTAINER ID   IMAGE              NAMES                STATUS
abc123def      ollama/ollama       tiny-llm-service     Up 5 seconds (healthy)
xyz789abc      llm-api-gateway     llm-api-gateway      Up 3 seconds (healthy)
```

### 2. Pull a Model (First Time Only)

```bash
# Download TinyLLaMA (lightweight, ~600MB)
docker exec -it tiny-llm-service ollama pull tinyllama

# Or use Mistral-7B (better quality, ~3.5GB)
docker exec -it tiny-llm-service ollama pull mistral
```

**Expected output:**
```
pulling manifest
pulling 3f1a0b76e4d7
```

### 3. Test Container

```bash
# Simple test
curl http://localhost:5000/health

# Inference test
curl -X POST http://localhost:5000/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "prompt": "What is AI?"
  }'
```

## Option 2: Manual Docker

### 1. Start Ollama

```bash
docker run -d \
  --name tiny-llm \
  -p 11434:11434 \
  -v llm_models:/root/.ollama/models \
  ollama/ollama
```

### 2. Pull Model

```bash
docker exec tiny-llm ollama pull mistral
```

### 3. Test

```bash
curl http://localhost:11434/api/tags
```

## Option 3: Podman (Rootless)

```bash
# Create pod
podman pod create --name tiny-llm -p 11434:11434

# Run container
podman run -d \
  --name ollama \
  --pod tiny-llm \
  -v llm_models:/root/.ollama/models \
  ollama/ollama

# Pull model
podman exec ollama ollama pull tinyllama
```

## Integrate with Agent Framework

### Use in FreeAgentPool

```python
from agent.agents import FreeAgentPool, OllamaAgent

# Create pool
pool = FreeAgentPool()

# Register container agent
container_agent = OllamaAgent(
    model="mistral:latest",
    base_url="http://localhost:11434"
)
pool.register_custom_agent("container", container_agent)

# Use it
result = await pool.execute_with_fallback(
    "Analyze this data",
    task_type="analysis"
)
```

### Use ContainerLLMPool

```python
from agent.containers import ContainerLLMPool

# Multiple containers (load balanced)
pool = ContainerLLMPool([
    "http://localhost:5000",
    "http://localhost:5001",
    "http://localhost:5002",
])

# Execute
result = await pool.execute("Your prompt here", model="mistral")

# Parallel execution
results = await pool.execute_parallel([
    "Prompt 1",
    "Prompt 2",
    "Prompt 3",
])
```

## Available Commands

### View Logs

```bash
# API Gateway logs
docker logs -f llm-api-gateway

# Ollama logs
docker logs -f tiny-llm

# Both
docker-compose logs -f
```

### Monitor Resources

```bash
docker stats tiny-llm llm-api-gateway
```

### List Models

```bash
curl http://localhost:5000/models
```

### Get Statistics

```bash
curl http://localhost:5000/stats
```

### Stop Containers

```bash
docker-compose down

# Or manual
docker stop tiny-llm llm-api-gateway
```

### Restart

```bash
docker-compose restart

# or
docker-compose down && docker-compose up -d
```

## Model Selection

### For Speed (Fastest)
```bash
docker exec tiny-llm ollama pull tinyllama
# ~600MB, 5-10 tok/s, 1GB RAM
```

### For Balanced Performance
```bash
docker exec tiny-llm ollama pull phi
# ~1.5GB, 8-15 tok/s, 2GB RAM
```

### For Best Quality
```bash
docker exec tiny-llm ollama pull mistral
# ~3.5GB, 10-20 tok/s, 4GB RAM
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs tiny-llm

# Check disk space
df -h /var/lib/docker

# Try pulling image
docker pull ollama/ollama:latest
```

### Out of Memory

```bash
# Reduce model or allocate more memory
docker update --memory 8g tiny-llm

# Restart
docker restart tiny-llm
```

### Slow Inference

```bash
# Check resource usage
docker stats tiny-llm

# Monitor system
top

# Try smaller model
docker exec tiny-llm ollama pull tinyllama
```

### Connection Refused

```bash
# Verify container is running
docker ps | grep tiny-llm

# Check port mapping
docker port tiny-llm

# Test connectivity
curl -v http://localhost:11434/api/tags
```

## Clean Up

```bash
# Stop containers
docker-compose down

# Remove volumes (deletes downloaded models)
docker volume rm llm_models

# Clean up all
docker-compose down -v
```

## Performance Tips

1. **Use lighter models for speed**: TinyLLaMA is fastest
2. **Allocate more memory for better quality**: Mistral needs 4GB
3. **Run health checks periodically**: Keeps containers responsive
4. **Use load balancing**: Distribute across multiple containers
5. **Cache results**: Store frequent inference results

## Next Steps

1. ✓ Start container: `docker-compose up -d`
2. ✓ Pull model: `docker exec tiny-llm ollama pull mistral`
3. ✓ Test: `curl http://localhost:5000/health`
4. ✓ Integrate: Use in agent framework
5. ✓ Monitor: Watch logs and stats

---

**Container is now ready for your agent framework!**

See CONTAINER_LLM_SERVICE.md for advanced configuration.
