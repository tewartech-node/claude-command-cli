# Archive: Legacy Code

This directory contains code that has been **deprecated** but kept for reference and testing.

## 🚫 Why These Are Here

### **cli-python-legacy/**
- **Status**: Deprecated (moved to `cli/go/`)
- **Why**: Python CLI was slow (2-3 second startup), large binary (200MB+), not suitable for 32-bit phones
- **Used By**: Legacy systems only
- **Keep Until**: All users migrated to Go CLI (target: Month 2)
- **Do Not**: Use as reference for new work

### **cli-node-test-harness/**
- **Status**: Test harness only (validates wire format)
- **Why**: Node.js implementation was abandoned early, only kept for regression testing
- **Used By**: Integration test suite (validates crypto compatibility)
- **Keep Until**: Go CLI is stable enough that wire format testing moves to `tests/`
- **Do Not**: Deploy this or use as API

### **cloudflare-worker-legacy/**
- **Status**: Obsolete (Cloudflare deployment not needed)
- **Why**: Canonical server is `warnetech_server` (Python), not Cloudflare Workers
- **Used By**: None (reference only)
- **Keep Until**: Decision made whether to support Cloudflare deployment
- **Do Not**: Use this - it's outdated and unsupported

---

## 📋 Migration Status

| Component | Status | Target Completion | Notes |
|-----------|--------|-------------------|-------|
| Python CLI | ❌ Deprecated | Month 2 | Users: switch to `cli/go/` |
| Node Test Suite | ⚠️ Partial | Month 1 | Migrate tests to `tests/` |
| Cloudflare Worker | ❌ Archived | TBD | Unclear if needed |

---

## 🔄 How to Use (if needed)

### Restore a file
```bash
git show archive/cli-python-legacy/main.py > warnetech_cli/main.py
```

### View history
```bash
git log archive/cli-python-legacy/
```

### Clean up (after migration complete)
```bash
# At end of Month 2:
git rm -r archive/
```

---

## 📚 Reference Only

These implementations show:
- How NOT to build a CLI (Python - too slow)
- Wire format validation (Node - but outdated)
- Cloudflare deployment (but no longer used)

**New work should reference `cli/go/` and `warnetech_server/` instead.**

---

**Last Updated**: 2026-08-11  
**Archived By**: Claude (AI Developer)
