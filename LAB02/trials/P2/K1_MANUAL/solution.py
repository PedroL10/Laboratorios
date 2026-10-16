def summarize_readings(readings, minimum):
    count = sum(1 for reading in readings if reading >= minimum)

    average = round(sum(readings) / len(readings), 2) if readings else 0

    maximum = max(readings) if readings else None

    return {
        "count": count,
        "average": average,
        "maximum": maximum
    }