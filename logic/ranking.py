def score_spot(spot):
    """Rule-based placeholder score, favoring close/cheap/confident spots.

    # TODO: replace with LLM/ML ranking model later
    """
    distance_score = 1 / (1 + spot["distance_km"])
    price_score = 1 / (1 + spot["price_per_hour"])
    confidence_score = spot["confidence"]

    return (distance_score * 0.4) + (price_score * 0.3) + (confidence_score * 0.3)


def rank_spots(spots):
    return sorted(spots, key=score_spot, reverse=True)
