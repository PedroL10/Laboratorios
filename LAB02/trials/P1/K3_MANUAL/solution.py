def delivery_windows(deliveries):
    if not isinstance(deliveries, list):
        raise TypeError("deliveries must be a list")

    zones = {}

    for delivery in deliveries:
        start = delivery["start"]
        end = delivery["end"]
        zone = delivery["zone"]

        if start >= end:
            raise ValueError("start must be less than end")

        if zone not in zones:
            zones[zone] = []

        zones[zone].append((start, end))

    result = {}

    for zone in sorted(zones):
        deliveries_zone = sorted(zones[zone])
        active = []
        max_windows = 0

        for start, end in deliveries_zone:
            # Remove as entregas que já terminaram
            active = [item for item in active if item > start]

            active.append(end)

            if len(active) > max_windows:
                max_windows = len(active)

        result[zone] = max_windows

    return result