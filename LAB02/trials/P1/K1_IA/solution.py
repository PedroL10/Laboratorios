def summarize_readings(readings, minimum):
    if not isinstance(readings, list):
        raise TypeError("readings must be a list")

    if not readings:
        return {
            "count": 0,
            "average": 0.0,
            "maximum": None,
        }

    count = sum(1 for reading in readings if reading >= minimum)
    average = round(sum(readings) / len(readings), 2)
    maximum = max(readings)

    return {
        "count": count,
        "average": average,
        "maximum": maximum,
    }

