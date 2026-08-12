# Agent Sourcing Framework

Enable The Brain to utilize free agents and autonomously create task-specific agents to source required data and meet system requirements.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│           AGENT SOURCING & SELF-CREATION FRAMEWORK              │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────┐
    │          Brain Needs Analysis Engine                 │
    │  Detects: "Need X data", "Require Y capability"     │
    └────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ↓            ↓            ↓
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │  Free   │  │ Paid    │  │ Create   │
   │ Agents  │  │ Agents  │  │ Custom   │
   │ Pool    │  │ Pool    │  │ Agent    │
   └────┬────┘  └────┬────┘  └────┬─────┘
        │            │            │
   ┌────┴────────────┴────────────┴─────┐
   │   Agent Selection & Execution      │
   │   (Cost-optimized routing)         │
   └────┬───────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │  Concurrent Agent Pool Execution  │
   │  (Parallel task processing)       │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │  Result Aggregation & Validation  │
   │  (Quality scoring)                │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │  Learning & Optimization          │
   │  (Future agent creation)          │
   └───────────────────────────────────┘
```

## 1. Free Agent Pool

### Available Free LLM Options

**Local/Self-Hosted (Zero Cost)**:
- **Ollama**: Easy local LLM runner (LLaMA 2, Mistral, Llama 2 7B/13B/70B)
- **LM Studio**: Desktop GUI + API for LLaMA, Mistral, Neural Chat
- **LocalAI**: Drop-in OpenAI API replacement, runs locally
- **GPT4All**: Lightweight models optimized for consumer hardware
- **vLLM**: Fast inference engine for open-source models

**Free API Tier Options** ($0 unless you exceed free tier):
- **Ollama** (self-hosted, truly free)
- **Groq** (Fast inference, free tier available)
- **HuggingFace Inference API** (Free tier: 1,000 daily requests)
- **Replicate** (Pay-per-use, free tier: $5 credit/month)
- **Together AI** (Free tier with rate limits)
- **OpenRouter** (Aggregates multiple models, free tier available)

### Agent Pool Architecture

```python
class FreeAgentPool:
    """Manages pool of free local and API-based agents"""
    
    def __init__(self):
        # Local agents (Ollama models)
        self.local_agents = {
            "mistral-7b": OllamaAgent("mistral:latest"),
            "llama2-13b": OllamaAgent("llama2:13b"),
            "neural-chat-7b": OllamaAgent("neural-chat"),
        }
        
        # Free API agents
        self.api_agents = {
            "groq-llama2": GroqAgent("llama2-70b-4096"),
            "huggingface-free": HuggingFaceAgent("tier": "free"),
            "openrouter-free": OpenRouterAgent("models": ["meta-llama/llama-2-13b"])
        }
        
        # Cost tracking
        self.cost_tracker = CostTracker()
        self.usage_metrics = {}
    
    async def select_agent(self, task_type, requirements):
        """Select best free agent for task"""
        candidates = self._filter_capable_agents(task_type, requirements)
        selected = self._rank_by_cost_efficiency(candidates)
        return selected
    
    async def execute_parallel(self, tasks):
        """Run multiple agents concurrently"""
        return await asyncio.gather(*[
            self._execute_with_fallback(task) for task in tasks
        ])
    
    async def _execute_with_fallback(self, task):
        """Try free agents first, fallback to paid if needed"""
        for agent in task.preferred_agents:
            try:
                result = await agent.execute(task)
                self.cost_tracker.log(agent.name, cost=0)
                return result
            except (RateLimit, Timeout):
                continue
        
        # Fallback to paid if free exhausted
        if task.allow_paid_fallback:
            result = await self.paid_agent_pool.execute(task)
            self.cost_tracker.log("paid_fallback", cost=result.cost)
            return result
        
        raise CapabilityError(f"Cannot execute {task.type}")
```

### Agent Capabilities Mapping

```python
agent_capabilities = {
    "mistral-7b": {
        "max_tokens": 4096,
        "latency_ms": 50,
        "cost": 0,
        "strengths": ["reasoning", "code", "analysis"],
        "throughput": "5 req/s local",
    },
    "llama2-13b": {
        "max_tokens": 4096,
        "latency_ms": 100,
        "cost": 0,
        "strengths": ["general", "conversation", "instruction-following"],
        "throughput": "3 req/s local",
    },
    "groq-llama2-70b": {
        "max_tokens": 4096,
        "latency_ms": 200,
        "cost": 0,  # Within free tier
        "strengths": ["complex reasoning", "long context"],
        "throughput": "30 req/s free tier",
        "rate_limit": "30 req/min free tier",
    },
    "huggingface-inference": {
        "max_tokens": 1024,
        "latency_ms": 500,
        "cost": 0,  # Free tier
        "strengths": ["text-generation", "summarization"],
        "throughput": "1000 req/day free tier",
    },
}
```

## 2. Self-Creating Agents

### Dynamic Agent Generation

**When Brain Detects Need**:
```
"I need to analyze financial data from 12 different sources"
            ↓
        Pattern Match: "data analysis" + "financial"
            ↓
        Generate Agent Prompt:
        "You are a financial data analyst agent.
         Your task: Fetch and analyze stock prices, crypto, commodities.
         Required: Data cleaning, trend detection, anomaly detection.
         Tools: Web scraping, data aggregation, statistical analysis.
         Success metric: Correlation coefficient > 0.85"
            ↓
        Instantiate Agent:
        - Use Mistral-7B for reasoning (free, local)
        - Use HuggingFace for embeddings (free tier)
        - Use web scraping tools (BeautifulSoup, Selenium)
        - Log to database for learning
            ↓
        Execute & Track Results
```

### Agent Factory Pattern

```python
class AgentFactory:
    """Creates specialized agents on-demand"""
    
    def create_agent(self, requirement_spec: dict):
        """
        Create an agent tailored to specific requirement
        
        Args:
            requirement_spec: {
                "task": "analyze financial data",
                "data_sources": ["stocks", "crypto"],
                "success_metric": "correlation > 0.85",
                "budget": "free_only" | "free_preferred" | "any",
                "latency_requirement": "realtime" | "hourly" | "daily"
            }
        """
        
        # Analyze requirement
        agent_type = self._classify_task(requirement_spec)
        
        # Select base model(s)
        base_model = self._select_base_model(
            agent_type,
            latency=requirement_spec.get("latency_requirement"),
            budget=requirement_spec.get("budget")
        )
        
        # Determine tools needed
        tools = self._determine_tools(agent_type, requirement_spec)
        
        # Generate system prompt
        system_prompt = self._generate_system_prompt(
            agent_type,
            requirement_spec,
            tools
        )
        
        # Create agent instance
        agent = SpecializedAgent(
            name=f"{agent_type}_{uuid4()}",
            model=base_model,
            system_prompt=system_prompt,
            tools=tools,
            success_metric=requirement_spec.get("success_metric")
        )
        
        # Register for tracking
        self.agent_registry.register(agent)
        
        return agent
    
    def _select_base_model(self, task_type, latency, budget):
        """Select best free model for task"""
        
        model_scores = {}
        
        for agent_name, specs in agent_capabilities.items():
            if budget == "free_only" and specs["cost"] > 0:
                continue
            
            score = 0
            
            # Strength matching
            if task_type in ["reasoning", "analysis"]:
                score += 3 if "reasoning" in specs["strengths"] else 0
            elif task_type in ["summarization", "extraction"]:
                score += 3 if "summarization" in specs["strengths"] else 0
            
            # Latency requirement
            if latency == "realtime" and specs["latency_ms"] < 500:
                score += 2
            
            # Throughput
            score += 1 if specs["throughput"] > 5 else 0
            
            model_scores[agent_name] = score
        
        return max(model_scores, key=model_scores.get)
    
    def _determine_tools(self, agent_type, requirement_spec):
        """Determine which tools agent needs"""
        
        tools = []
        
        # Data access tools
        if any(s in agent_type for s in ["data", "scrape", "fetch"]):
            tools.extend([
                WebScraperTool(),
                DataFetchTool(),
                APICallerTool()
            ])
        
        # Analysis tools
        if "analyze" in agent_type:
            tools.extend([
                DataAnalysisTool(),
                StatisticalTool(),
                VisualizationTool()
            ])
        
        # Correlation/pattern tools
        if requirement_spec.get("success_metric") and "correlation" in requirement_spec["success_metric"]:
            tools.append(CorrelationTool())
        
        # Storage tools
        tools.extend([
            DatabaseStorageTool(),
            CacheTool()
        ])
        
        return tools
    
    def _generate_system_prompt(self, agent_type, requirement_spec, tools):
        """Generate specialized system prompt"""
        
        return f"""You are a {agent_type} agent.

Your primary objective: {requirement_spec.get('task', 'Complete assigned task')}

Required capabilities:
- Data sources: {', '.join(requirement_spec.get('data_sources', []))}
- Success metric: {requirement_spec.get('success_metric', 'Task completion')}
- Latency requirement: {requirement_spec.get('latency_requirement', 'Best effort')}

Available tools:
{self._format_tools(tools)}

Instructions:
1. Break down task into sub-tasks
2. Fetch required data using appropriate tools
3. Validate data quality
4. Perform required analysis
5. Report results with confidence scores
6. Log any errors or limitations

Success = Meeting the success metric specified above.
Failure = Not meeting success metric, or encountering unrecoverable errors.

Always prioritize data quality over speed.
Always validate assumptions before proceeding.
"""
```

## 3. Automatic Source Detection & Bridging

### Source Discovery System

```python
class SourceDiscoveryEngine:
    """Automatically discover and bridge to required data sources"""
    
    def __init__(self):
        self.known_sources = {
            "financial": ["yahoo-finance", "alpha-vantage", "crypto-compare"],
            "news": ["hackernews", "newsapi", "reddit"],
            "weather": ["openweathermap", "weatherapi"],
            "social": ["twitter-api", "reddit-api"],
            "technical": ["github-api", "stack-overflow"],
        }
        
        self.source_connectors = {}
    
    def discover_sources(self, requirement):
        """Find relevant data sources for requirement"""
        
        # Parse requirement
        keywords = self._extract_keywords(requirement)
        categories = self._map_to_categories(keywords)
        
        # Find matching sources
        relevant_sources = []
        for category in categories:
            if category in self.known_sources:
                relevant_sources.extend(self.known_sources[category])
        
        return self._deduplicate_and_rank(relevant_sources)
    
    def bridge_to_source(self, source_name, free_only=True):
        """
        Create or retrieve connector to data source
        
        Strategy:
        1. Try free/open API first
        2. Use Ollama-based scraper if no API
        3. Use BeautifulSoup web scraping
        4. Fallback to paid API if necessary
        """
        
        if source_name in self.source_connectors:
            return self.source_connectors[source_name]
        
        source_strategy = self._determine_strategy(source_name, free_only)
        
        connector = self._create_connector(source_name, source_strategy)
        self.source_connectors[source_name] = connector
        
        return connector
    
    def _determine_strategy(self, source_name, free_only):
        """Determine best free strategy to access source"""
        
        strategies = {
            "hackernews": "free_api",  # No auth required
            "weather": "free_api",  # OpenWeatherMap free tier
            "crypto": "websocket",  # Free WebSocket streams
            "twitter": "rss_scrape",  # Free RSS feeds (limited)
            "reddit": "free_api",  # Reddit API free tier
            "github": "free_api",  # GitHub API free tier
            "stocks": "web_scrape",  # Yahoo Finance web scraping
        }
        
        return strategies.get(source_name, "web_scrape")
```

## 4. Cost Optimization & Fallback Chain

### Intelligent Fallback Mechanism

```python
class CostOptimizedExecutor:
    """Route tasks to free agents, fallback to paid intelligently"""
    
    async def execute(self, task, budget_limit=0):  # $0 = free only
        """
        Execute task with cost-optimized routing
        
        Chain:
        1. Local free agents (Ollama) - $0
        2. Free API tier agents (Groq, HuggingFace) - $0
        3. Batch processing during off-peak - $0-1
        4. Paid agents if budget allows
        """
        
        results = []
        cost_so_far = 0
        
        # Try local agents first
        local_result = await self._try_local_execution(task)
        if local_result and local_result.quality_score > 0.7:
            self.cost_tracker.log("local_agent", cost=0)
            return local_result
        
        # Try free API agents
        free_result = await self._try_free_api_execution(task)
        if free_result and free_result.quality_score > 0.7:
            self.cost_tracker.log("free_api_agent", cost=0)
            return free_result
        
        # If within budget, try paid
        if budget_limit > 0 and cost_so_far < budget_limit:
            paid_result = await self._try_paid_execution(task)
            cost = paid_result.metadata.cost
            if cost <= (budget_limit - cost_so_far):
                self.cost_tracker.log("paid_agent", cost=cost)
                return paid_result
        
        # Last resort: batch and retry
        return await self._batch_retry(task)
    
    async def _try_local_execution(self, task):
        """Run on local Ollama agents"""
        try:
            agent = self.local_agent_pool.select(task.type)
            result = await agent.execute(task, timeout=10)
            return result
        except (Timeout, OutOfMemory):
            return None
    
    async def _try_free_api_execution(self, task):
        """Run on free tier API agents"""
        try:
            agent = self.free_api_pool.select(task.type)
            result = await agent.execute(task, timeout=30)
            return result
        except (RateLimit, QuotaExceeded):
            return None
    
    async def _batch_retry(self, task):
        """Queue for batch processing during off-peak hours"""
        batch_job = self.batch_processor.queue(
            task,
            priority="low",
            execute_after_hours=True
        )
        return await batch_job.wait()
```

## 5. Learning & Agent Evolution

### Agent Performance Tracking

```python
class AgentPerformanceTracker:
    """Learn from agent performance and optimize future selection"""
    
    def record_execution(self, agent, task, result):
        """Log agent performance metrics"""
        
        metrics = {
            "agent_name": agent.name,
            "task_type": task.type,
            "duration_ms": result.duration_ms,
            "tokens_used": result.tokens_used,
            "quality_score": result.quality_score,
            "cost": result.cost,
            "success": result.success,
            "timestamp": datetime.now(),
        }
        
        # Store in database
        self.db.insert("agent_performance", metrics)
        
        # Update agent rating
        self._update_agent_rating(agent, result)
    
    def get_best_agent_for_task(self, task_type, budget=0):
        """Recommend best agent based on historical performance"""
        
        query = """
        SELECT agent_name, AVG(quality_score) as avg_quality,
               AVG(duration_ms) as avg_duration, COUNT(*) as executions
        FROM agent_performance
        WHERE task_type = %s AND cost <= %s
        GROUP BY agent_name
        ORDER BY (avg_quality * 0.7 - avg_duration/1000 * 0.3) DESC
        """
        
        results = self.db.query(query, [task_type, budget])
        if results:
            return results[0]['agent_name']
        
        return None
    
    def identify_new_agent_needs(self):
        """Detect when new agent specialization would help"""
        
        # Find tasks with low success rates
        low_success = self.db.query("""
        SELECT task_type, AVG(quality_score) as avg_quality, COUNT(*) as count
        FROM agent_performance
        WHERE success = FALSE
        GROUP BY task_type
        HAVING count > 5 AND avg_quality < 0.6
        """)
        
        # Recommend new agent creation
        for task in low_success:
            self.recommendation_queue.put({
                "action": "create_specialized_agent",
                "task_type": task['task_type'],
                "reason": f"Low success rate: {task['avg_quality']}"
            })
```

## 6. Integration with Brain

### Automatic Requirement Detection

```python
class BrainRequirementDetector:
    """Detects when Brain needs agent assistance"""
    
    def monitor_brain_state(self):
        """Continuously monitor Brain for emerging needs"""
        
        while True:
            state = self.brain.get_current_state()
            
            # Check various requirement triggers
            if state['decision_success_rate'] < 0.70:
                self._trigger_agent("improve_decision_quality", budget=0)
            
            if state['database_size_mb'] > 500:
                self._trigger_agent("optimize_storage", budget=0)
            
            if state['telemetry_gap_hours'] > 6:
                self._trigger_agent("fetch_missing_telemetry", budget=0)
            
            if state['code_issues_critical'] > 0:
                self._trigger_agent("analyze_code_issues", budget=0)
            
            if state['pattern_extraction_rate'] < 1.0 / 86400:  # < 1/day
                self._trigger_agent("extract_behavioral_patterns", budget=0)
            
            sleep(60)
    
    def _trigger_agent(self, requirement, budget):
        """Trigger creation and execution of specialized agent"""
        
        agent = self.agent_factory.create_agent({
            "task": requirement,
            "budget": "free_only" if budget == 0 else f"${budget}",
            "latency_requirement": "hourly"
        })
        
        result = asyncio.run(agent.execute(
            context=self.brain.get_current_state()
        ))
        
        self.brain.apply_agent_results(requirement, result)
```

## 7. Cost Analysis

### Free Option - $0 Forever

**Monthly Operational Cost Breakdown**:

| Component | Solution | Cost | Throughput |
|-----------|----------|------|-----------|
| LLM Inference | Ollama (local) | $0 | 3-5 req/s |
| Additional Models | LM Studio | $0 | Local only |
| Free API Tier | Groq, HF, OR | $0 | 30-100 req/min |
| Data Sourcing | Web scraping | $0 | Limited by bandwidth |
| Storage | Local + S3 Free | $0 first 5GB | - |
| Compute | Your hardware | $0 | Variable |
| **Total** | **All free options** | **$0** | **5-30 req/s** |

**Paid Option Upgrade Path** ($50-200/month):

| Component | Solution | Cost | When |
|-----------|----------|------|------|
| Faster LLM | Claude API | $10-50/mo | When local insufficient |
| More models | OpenRouter | $20-100/mo | Testing different models |
| Premium API | NewsAPI, Alpha Vantage | $15-50/mo | Better data quality |
| Cloud hosting | AWS | $50-300/mo | When scaling needed |

**Cost Ratio**: Free operations = 100% free, Paid operations = 10-20% of current Claude API usage

## 8. Implementation Roadmap

### Phase 1 (Week 1-2): Free Agent Pool Foundation
- [ ] Deploy Ollama locally with Mistral-7B, LLaMA 2
- [ ] Implement FreeAgentPool class
- [ ] Add Groq free API integration
- [ ] Basic agent selection logic
- [ ] Cost tracking system

### Phase 2 (Week 3-4): Agent Factory & Self-Creation
- [ ] Implement AgentFactory class
- [ ] Dynamic prompt generation system
- [ ] Tool binding framework
- [ ] Agent registry and lifecycle management
- [ ] Performance tracking

### Phase 3 (Week 5-6): Brain Integration
- [ ] Requirement detection in DiagnosticEngine
- [ ] Automatic agent triggering
- [ ] Result integration back to Brain
- [ ] Learning & optimization

### Phase 4 (Week 7-8): Advanced Features
- [ ] Multi-agent coordination
- [ ] Hierarchical agent spawning
- [ ] Cross-agent communication
- [ ] Emergent capability detection

## 9. Example: Meeting "Storage Optimization" Requirement

```python
# Brain detects: Database size > 500MB
brain_state = {
    "database_size_mb": 520,
    "free_disk_space_mb": 2000,
    "performance_score": 0.75,
}

# Automatically creates agent
agent = agent_factory.create_agent({
    "task": "analyze database and recommend optimizations",
    "data_sources": ["internal_database"],
    "success_metric": "Find optimizations yielding >20% reduction",
    "budget": "free_only",
    "latency_requirement": "hourly"
})

# Agent execution (using free Mistral-7B locally)
result = await agent.execute(brain_state)

# Result: "Compression: 6.2x, Archival: 125 old records, VACUUM: 15% reclaim"
# Cost: $0
# Time: 2 minutes

# Brain applies: Runs compression, archival, VACUUM
# Storage improves: 520MB → 312MB
# Cost: $0
```

## Success Metrics

A successful free agent system provides:

✅ **Cost**: Zero operational cost for common tasks
✅ **Latency**: 1-10 second response time for most agent tasks
✅ **Throughput**: 5-30 concurrent agents
✅ **Quality**: 75%+ success rate on first attempt
✅ **Autonomy**: Creates specialized agents without human intervention
✅ **Learning**: Gets better at agent selection over time

## Next Steps

1. Deploy Ollama with free models locally
2. Implement FreeAgentPool with fallback chain
3. Create AgentFactory with dynamic prompt generation
4. Integrate with DiagnosticEngine for automatic triggering
5. Track performance and optimize agent selection

---

**Status**: Framework designed, ready for implementation
**Estimated Effort**: 3-4 weeks for full integration
**Cost**: $0 (uses only free/self-hosted options)
**Payoff**: Autonomous agent ecosystem, unlimited task scaling
