"""Vision-based extraction: PDF page → structured cabinet rows.

This is the only AI-dependent step in the pipeline. Stage 1 uses Claude vision
via the Anthropic API. Stage 2+ may add fallbacks (PDF→DXF + symbol templates,
or native DWG block-name parsing).
"""
