## Summary

Add three **Docs-Only** projects for CUDA Toolkit, Ascend CANN, and MindSpore. Each project will track official documentation only (no release notes), display a Chinese name, and participate in the normal sync cadence.

## Decision

We will implement **Docs-Only projects**:
- Release area disabled
- Docs area enabled
- Official documentation URL as the single source of truth
- Chinese display names for the UI

## Projects to Add

1. **CUDA 工具链**
   - Docs: `https://docs.nvidia.com/cuda/`
   - Release: disabled

2. **昇腾 CANN**
   - Docs: `https://www.hiascend.com/document`
   - Release: disabled

3. **MindSpore**
   - Docs: `https://www.mindspore.cn/docs/`
   - Release: disabled

## Scope

In scope:
- Add the three projects into `projects.json`
- Generate crawl profiles for each docs-only project
- Ensure release area is disabled and docs area enabled

Out of scope:
- Adding non-GitHub release sources
- Any new crawling logic beyond existing docs crawler
