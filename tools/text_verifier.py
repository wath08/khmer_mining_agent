import re
import config


def verify_text(text: str) -> dict:
    """
    Verifies if the text meets length and Khmer character ratio requirements.
    Returns a dict with 'is_valid', 'reason', 'khmer_ratio', 'length'.
    """
    if not text:
        return {"is_valid": False, "reason": "Empty text", "khmer_ratio": 0.0, "length": 0}

    length = len(text.strip())
    min_length = getattr(config, 'MIN_TEXT_LENGTH', 150)
    min_ratio = getattr(config, 'MIN_KHMER_RATIO', 0.50)

    if length < min_length:
        return {
            "is_valid": False,
            "reason": f"Text too short ({length} chars < {min_length})",
            "khmer_ratio": 0.0,
            "length": length
        }

    # Extract Khmer characters and Latin characters
    khmer_chars = re.findall(r'[\u1780-\u17ff\u19e0-\u19ff]', text)
    latin_chars = re.findall(r'[a-zA-Z]', text)

    total_letters = len(khmer_chars) + len(latin_chars)

    # Calculate ratio of Khmer letters relative to total letters
    if total_letters > 0:
        khmer_letter_ratio = len(khmer_chars) / total_letters
    else:
        khmer_letter_ratio = 0.0

    # Also compute overall string ratio
    overall_ratio = len(khmer_chars) / length

    # Pass if either the letter ratio or the overall ratio meets threshold
    effective_ratio = max(khmer_letter_ratio, overall_ratio)

    if effective_ratio < min_ratio:
        return {
            "is_valid": False,
            "reason": (
                f"Khmer ratio too low "
                f"(letter_ratio: {khmer_letter_ratio:.2f}, overall: {overall_ratio:.2f} < {min_ratio})"
            ),
            "khmer_ratio": effective_ratio,
            "length": length
        }

    # Reject obvious Hub/Listing Pages with repeated navigation UI phrases
    if text.count("អានបន្ត") > 5 or text.count("ទាញយក") > 5 or text.count("មើលឯកសារ") > 5:
        return {
            "is_valid": False,
            "reason": "Looks like a hub/listing page (Repeated UI buttons)",
            "khmer_ratio": effective_ratio,
            "length": length
        }

    return {"is_valid": True, "reason": "Valid", "khmer_ratio": effective_ratio, "length": length}
