"""Excel template adapter — write inputs, run recalc, read computed outputs.

The customer's Excel template is the source of truth for math. We populate
input sheets (장등록, 상품등록, 기초입력), trigger LibreOffice recalc, and
read back the computed values for the web UI.
"""
