def delivery_windows(deliveries):
    windows_by_zone = {}

    for delivery in deliveries:
        if "zone" not in delivery:
            raise KeyError("zone")
        start = delivery["start"]
        end = delivery["end"]
        zone = delivery["zone"]
        if start >= end:
            raise ValueError("start must be less than end")
        windows_by_zone.setdefault(zone, []).append((start, end))

    result = {}
    for zone in sorted(windows_by_zone):
        intervals = sorted(windows_by_zone[zone])
        active_ends = []
        max_windows = 0
        for start, end in intervals:
            active_ends = [e for e in active_ends if e > start]
            active_ends.append(end)
            max_windows = max(max_windows, len(active_ends))
        result[zone] = max_windows

    return result