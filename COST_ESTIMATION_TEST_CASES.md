# Claude API Cost Estimation — Test Case Generation (10 Test Cases)

**Pipeline:** `POST /analyze-ticket/test-cases`  
**Task:** Generate 10 test cases per JIRA ticket (new feature or bug)  
**Date:** May 2026  

---

## 1. How the Pipeline Consumes Tokens

Every call to `/analyze-ticket/test-cases` sends one request to the Claude API.  
The request is split into two parts:

```
┌─────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT  (fixed per deployment, cacheable)        │
│  • Role definition + rules (~201 tokens)                │
├─────────────────────────────────────────────────────────┤
│  USER MESSAGE   (varies per ticket)                     │
│  • Graph DB schema              ~89 tokens  (cacheable) │
│  • User template structure      ~93 tokens  (cacheable) │
│  • JIRA ticket text           100–450 tokens            │
│  • Code context (semantic +                             │
│    graph traversal)           510–1000 tokens           │
└─────────────────────────────────────────────────────────┘
         │
         ▼  Claude generates
┌─────────────────────────────────────────────────────────┐
│  OUTPUT (test cases document)                           │
│  10 test cases × 200–350 tokens each  = 2,000–3,500 tok│
└─────────────────────────────────────────────────────────┘
```

**Fixed (cacheable) tokens:** `383` — system prompt + schema + template.  
These never change between calls and can be served from Anthropic's prompt cache at **10% of normal input price**.

---

## 2. Model Pricing Reference

| Model | Input ($/1M tokens) | Output ($/1M tokens) | Speed | Quality |
|---|---|---|---|---|
| `claude-opus-4-7` | $15.00 | $75.00 | Slowest | Highest |
| `claude-sonnet-4-6` *(current default)* | $3.00 | $15.00 | Balanced | High |
| `claude-haiku-4-5` | $0.80 | $4.00 | Fastest | Good |

**Prompt cache pricing (applied to the 383 fixed tokens after first call):**  
Cache write: +25% on first call · Cache read: −90% on subsequent calls · TTL: 5 minutes

---

## 3. Ticket Scenarios & Token Breakdown

### Scenario A — Simple Bug Fix / Small Change
> e.g., missing `/365` divisor in a calculation function

| Component | Chars | Tokens |
|---|---|---|
| System prompt | 805 | 201 |
| Template + schema | 730 | 183 |
| Ticket text (key, type, summary, short desc) | ~400 | 100 |
| Code context (5 semantic hits + 8 functions) | ~2,040 | 510 |
| **Total Input** | | **994** |
| Output (10 test cases, brief) | | **2,000** |

### Scenario B — Medium Feature / Complex Bug
> e.g., new repayment flow or Kafka consumer backoff logic

| Component | Chars | Tokens |
|---|---|---|
| System prompt | 805 | 201 |
| Template + schema | 730 | 183 |
| Ticket text (with detailed description) | ~900 | 225 |
| Code context (10 semantic hits + 15 functions) | ~3,000 | 750 |
| **Total Input** | | **1,359** |
| Output (10 test cases, moderate detail) | | **2,800** |

### Scenario C — Large Feature / Significant Refactor
> e.g., new authentication module or multi-repo integration

| Component | Chars | Tokens |
|---|---|---|
| System prompt | 805 | 201 |
| Template + schema | 730 | 183 |
| Ticket text (full ADF description) | ~1,800 | 450 |
| Code context (15 semantic hits + 20 functions) | ~4,000 | 1,000 |
| **Total Input** | | **1,834** |
| Output (10 test cases, detailed + edge cases) | | **3,500** |

---

## 4. Cost Per API Call

### Without Prompt Caching (first call or cache miss)

| Model | Scenario A | Scenario B | Scenario C |
|---|---|---|---|
| `claude-opus-4-7` | $0.1649 | $0.2304 | $0.2900 |
| `claude-sonnet-4-6` | $0.0330 | $0.0461 | $0.0580 |
| `claude-haiku-4-5` | $0.0088 | $0.0123 | $0.0155 |

### With Prompt Caching (repeat calls, 383 fixed tokens cached)

| Model | Scenario A | Scenario B | Scenario C | Cache Saving |
|---|---|---|---|---|
| `claude-opus-4-7` | $0.1597 | $0.2252 | $0.2848 | ~$0.005/call |
| `claude-sonnet-4-6` | $0.0319 | $0.0450 | $0.0570 | ~$0.001/call |
| `claude-haiku-4-5` | $0.0085 | $0.0120 | $0.0152 | ~$0.0003/call |

> **Note:** Cache savings grow significantly when you send many tickets in the same 5-minute window (e.g., batch processing). The 383 fixed tokens are written once and read at 90% discount for every subsequent call in that window.

---

## 5. Monthly Cost Projections

*Based on Scenario B (medium ticket) as the realistic baseline.*

| Calls / Month | `claude-opus-4-7` | `claude-sonnet-4-6` | `claude-haiku-4-5` |
|---|---|---|---|
| 10 | $2.30 | $0.46 | $0.12 |
| 50 | $11.52 | $2.30 | $0.61 |
| 100 | $23.04 | $4.61 | $1.23 |
| 500 | $115.19 | $23.04 | $6.15 |
| 1,000 | $230.37 | $46.07 | $12.29 |
| 5,000 | $1,151.85 | $230.35 | $61.45 |

---

## 6. Quality vs Cost Trade-off

| | `claude-haiku-4-5` | `claude-sonnet-4-6` | `claude-opus-4-7` |
|---|---|---|---|
| **Test case depth** | Generic steps, shallow preconditions | Concrete, references real function names | Most detailed, catches subtle edge cases |
| **Code context usage** | May miss nuanced graph context | Uses context well | Deep reasoning over call graph |
| **Regression test quality** | Basic | Good | Excellent |
| **Edge case coverage** | Misses some | Catches most | Comprehensive |
| **Relative cost** | 1× | 3.75× | 23.6× |
| **Latency** | ~5–10s | ~15–30s | ~30–60s |
| **Best for** | High-volume / quick triage | Day-to-day dev workflow | Critical releases / compliance |

---

## 7. Configuration Changes to Generate 10 Test Cases

The current implementation generates **5** test cases (`max_tokens=1500`).  
To switch to **10**, update these two values in [app/test_case_generator.py](app/test_case_generator.py):

```python
# In _SYSTEM_PROMPT — change the rules line:
"Your task: produce a concise Markdown test-case document with EXACTLY 10 test cases"

# In generate() — increase token budget:
test_cases_md = self.llm_client.complete(_SYSTEM_PROMPT, user_message, max_tokens=3000)
```

And in `llm_client.py`, the `complete()` signature already accepts `max_tokens` as a parameter, so no change needed there.

**Impact on cost:** Doubling from 5 → 10 test cases roughly doubles the output tokens only (input is unchanged). At Scenario B on Sonnet 4.6:
- 5 TCs:  ~1,400 output tokens → **$0.024/call**
- 10 TCs: ~2,800 output tokens → **$0.046/call**

---

## 8. Cost Optimisation Strategies

### A. Prompt Caching (immediate, ~2–3% saving)
The system prompt and graph schema are identical across all calls.  
Enable caching by using Anthropic's cache-control header:

```python
# In llm_client.py AnthropicLLMClient.complete()
response = self.client.messages.create(
    model=self.settings.llm_model,
    max_tokens=max_tokens,
    system=[{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"},   # ← add this
    }],
    messages=[{"role": "user", "content": user_message}],
)
```

### B. Reduce Code Context (5–15% saving)
The current code context cap is `hits[:5]` with `text[:200]`.  
Reducing to `hits[:3]` + `text[:150]` saves ~150 input tokens per call with minimal quality impact for simple bugs.

### C. Model Routing by Ticket Type (40–60% saving)
Route ticket type to the appropriate model automatically:

```python
def select_model(ticket_type: str, priority: str) -> str:
    if ticket_type == "Bug" and priority in ("Highest", "High"):
        return "claude-sonnet-4-6"      # thorough for critical bugs
    if ticket_type in ("Task", "Sub-task"):
        return "claude-haiku-4-5"       # cheap for low-stakes tickets
    if ticket_type == "Epic":
        return "claude-opus-4-7"        # deep reasoning for large features
    return "claude-sonnet-4-6"          # default
```

### D. Batch Processing with Cache Warmup
If generating test cases for multiple tickets back-to-back, send them within 5 minutes of each other so the fixed 383-token system prompt stays in cache.

---

## 9. Recommended Setup by Team Size

| Team | Volume | Recommended Model | Est. Monthly Cost |
|---|---|---|---|
| Solo developer | ~10 calls/mo | `claude-haiku-4-5` | < $0.15 |
| Small team (5–10 devs) | ~100 calls/mo | `claude-sonnet-4-6` | ~$4.61 |
| Mid-size team (20–50 devs) | ~500 calls/mo | `claude-sonnet-4-6` | ~$23.04 |
| Enterprise / CI pipeline | ~1,000+ calls/mo | Model routing (Strategy C above) | ~$15–47 |

---

## 10. Summary

| | `claude-haiku-4-5` | `claude-sonnet-4-6` | `claude-opus-4-7` |
|---|---|---|---|
| **Cost per 10 TCs (medium ticket)** | ~$0.012 | ~$0.046 | ~$0.230 |
| **100 calls/month** | $1.23 | $4.61 | $23.04 |
| **Output quality** | Good | **Recommended** | Best |

**Recommendation:** Use `claude-sonnet-4-6` as the default — it produces detailed, code-aware test cases that reference actual function names and file paths from the graph context, at a cost that stays under $50/month for most teams. Reserve `claude-opus-4-7` for Epic-level tickets or pre-release test generation where depth matters. Use `claude-haiku-4-5` for automated CI pipelines that generate quick smoke-test scaffolding at scale.
