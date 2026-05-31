from __future__ import annotations


def compute_market_trend(series: dict[str, list[tuple]]) -> dict:
    results: dict = {}

    for metric, points in series.items():
        valid = [(p, v) for (p, v) in points if v is not None]

        if not valid:
            results[metric] = {"latest": None, "direction": "없음"}
            continue

        latest_val = float(valid[-1][1])

        if len(valid) == 1:
            results[metric] = {"latest": latest_val, "direction": "없음"}
            continue

        earliest_val = float(valid[0][1])

        if earliest_val == 0:
            direction = "유지"
        else:
            change = (latest_val - earliest_val) / earliest_val
            if change > 0.05:
                direction = "증가"
            elif change < -0.05:
                direction = "감소"
            else:
                direction = "유지"

        results[metric] = {"latest": latest_val, "direction": direction}

    unsold_up = results.get("unsold", {}).get("direction") == "증가"
    tx_down = results.get("apt_tx_monthly", {}).get("direction") == "감소"

    if unsold_up and tx_down:
        summary = "미분양 증가·거래량 감소 → 역전세 주의"
    else:
        parts = [f"{m}: {v['direction']}" for m, v in results.items()]
        summary = ", ".join(parts) if parts else "데이터 없음"

    results["summary"] = summary
    return results
