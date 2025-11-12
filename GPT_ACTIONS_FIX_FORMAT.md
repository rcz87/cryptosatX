# 🚨 FIX GPT ACTIONS - FORMAT ARGS

## MASALAH
GPT tidak mengirim parameter `args` dengan benar ke API.

## ROOT CAUSE
GPT Actions interpreter kadang "flatten" object structure dan put symbol di top level instead of inside args.

## SOLUSI: Update GPT Instructions

### ADD THIS SECTION (Copy Paste ke GPT Instructions):

```
## 🚨 CRITICAL API FORMAT RULES

When calling the "invoke" action, follow this EXACT structure:

CORRECT FORMAT (ALWAYS USE THIS):
{
  "operation": "signals.get",
  "args": {
    "symbol": "SOL"
  }
}

WRONG FORMATS (NEVER USE THESE):
❌ {"operation": "signals.get", "symbol": "SOL"}
❌ {"operation": "signals.get", "args": {}}
❌ {"operation": "signals.get"}

KEY RULES:
1. "args" MUST be an object {}
2. "symbol" MUST be INSIDE the "args" object
3. NEVER put symbol at the top level
4. NEVER send empty args

EXAMPLES FOR EACH OPERATION:

Trading Signals:
✅ {"operation": "signals.get", "args": {"symbol": "BTC"}}
✅ {"operation": "signals.get", "args": {"symbol": "SOL"}}
✅ {"operation": "signals.get", "args": {"symbol": "ETH"}}

Smart Money:
✅ {"operation": "smart_money.scan", "args": {}}
✅ {"operation": "smart_money.analyze", "args": {"symbol": "AXS"}}

MSS Discovery:
✅ {"operation": "mss.discover", "args": {"min_mss_score": 75}}
✅ {"operation": "mss.analyze", "args": {"symbol": "PEPE"}}

LunarCrush:
✅ {"operation": "lunarcrush.coin", "args": {"symbol": "DOGE"}}

VERIFICATION CHECKLIST:
Before calling invoke action, verify:
□ Is "args" present?
□ Is "args" an object (not null)?
□ Is "symbol" inside "args" object?
□ Did I avoid putting symbol at top level?

If you get error "Missing required argument 'symbol'", it means you sent the WRONG format.
Re-read this section and use the CORRECT format above.
```

## CARA APPLY:

1. Buka GPT Editor → Instructions
2. Tambahkan section di atas ke bagian atas instructions
3. Save
4. Test dengan prompt: "Analisa SOL"
5. Verify GPT call invoke action dengan format benar

## ALTERNATIVE: Test Manual di GPT

Jika masih error, test dengan prompt yang sangat spesifik:

```
Call the invoke action with this EXACT JSON structure:
{
  "operation": "signals.get",
  "args": {
    "symbol": "SOL"
  }
}

Do NOT modify the structure. The args field MUST contain an object with symbol inside it.
```

## VERIFY API WORKING

Test langsung via cURL untuk confirm API berfungsi:

```bash
curl -X POST "https://guardiansofthetoken.org/invoke" \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "args": {"symbol": "SOL"}}'
```

Expected response:
```json
{
  "ok": true,
  "data": {
    "symbol": "SOL",
    "signal": "NEUTRAL",
    "score": 48.9,
    "price": 155.1,
    ...
  }
}
```

## TROUBLESHOOTING

Jika masih error setelah update instructions:

1. **Delete dan Re-import Action**
   - Di GPT Actions, hapus action yang ada
   - Re-import dari: `https://guardiansofthetoken.org/invoke/schema`

2. **Cek Debug Panel**
   - Lihat exact request yang dikirim GPT
   - Apakah ada field "args"?
   - Apakah "symbol" di dalam "args"?

3. **Try Different Prompt**
   Instead of: "Analisa SOL"
   Try: "Get trading signal for SOL using the invoke action with symbol SOL in the args object"

4. **Last Resort: Use REST API**
   Jika RPC tetap bermasalah, fallback ke REST:
   ```
   GET https://guardiansofthetoken.org/signals/SOL
   ```
