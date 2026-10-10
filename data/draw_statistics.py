def extract_draw_statistics(draw: dict, draw_no: int = 0) -> tuple[int | None, list[tuple[int, int, int]] | None]:
    """Extract total sales and rank statistics from supported draw formats."""
    sales = next(
        (draw[key] for key in ("total_sales_amount", "totalSales", "totSellamnt", "tot_sellamnt")
         if draw.get(key) is not None),
        None,
    )
    total_sales = int(sales) if sales is not None else None

    divisions = draw.get("divisions")
    if isinstance(divisions, list):
        stats = []
        for division in divisions[:5]:
            division = division if isinstance(division, dict) else {}
            prize = int(division.get("prize") or 0)
            winners = int(division.get("winners") or 0)
            stats.append((prize * winners, winners, prize))
        stats.extend([(0, 0, 0)] * (5 - len(stats)))
        return total_sales, stats

    prizes = draw.get("prizes")
    if isinstance(prizes, list):
        stats = [(0, 0, 0) for _ in range(5)]
        has_stats = False
        for prize in prizes:
            if not isinstance(prize, dict):
                continue
            try:
                rank = int(prize.get("rank"))
            except (TypeError, ValueError):
                continue
            if not 1 <= rank <= 5:
                continue
            winners = int(prize.get("winners") or 0)
            per_winner = int(prize.get("prizePerWinner") or 0)
            if rank == 4 and per_winner == 0:
                per_winner = 50000
            elif rank == 5 and per_winner == 0:
                per_winner = 10000 if draw_no <= 87 else 5000
            stats[rank - 1] = (winners * per_winner, winners, per_winner)
            has_stats = True
        return total_sales, stats if has_stats else None

    return total_sales, None
