from pathlib import Path
from dataclasses import dataclass
import numpy as np


@dataclass
class DatasetSplit:
    texts: list[str]
    labels: list[int]  # 0 = Real / Legitimate, 1 = Fake / Misinformation


def get_curated_benchmark_samples() -> tuple[DatasetSplit, DatasetSplit]:
    """Provides a deterministic benchmark split of authentic news and deceptive/fabricated claims
    based on standard misinformation taxonomies (for local evaluation and unit testing)."""
    train_texts = [
        # Real (0)
        "The central bank held interest rates steady today following its monthly monetary policy meeting.",
        "Scientists at the meteorological department forecast moderate rainfall across the coastal regions this weekend.",
        "The international trade summit concluded with bilateral agreements on semiconductor supply chains.",
        "Researchers published peer-reviewed findings on solar cell efficiency in the journal Nature Energy.",
        "The municipal corporation announced road repairs scheduled on the ring road starting next Monday.",
        "The national railway service launched electric locomotive trials on the northern freight corridor.",
        "The health ministry advised routine seasonal flu immunizations ahead of the winter season.",
        "Quarterly GDP growth figures were published by the national statistics office showing steady expansion.",
        # Fake / Sensational (1)
        "SHOCKING: Secret underground alien base uncovered beneath the presidential palace!",
        "URGENT ALERT: Drinking boiled garlic water cures all known viral diseases overnight!",
        "Government secretly putting microscopic tracking chips inside routine drinking water supplies!",
        "Billionaire reveals secret miracle investment that guarantees 500 percent returns in 24 hours!",
        "NASA whistleblower admits moon landing was staged on a Hollywood film studio soundstage!",
        "Doctors stunned as 100-year-old fruit eliminates cancer cells in just twenty minutes!",
        "Mysterious time traveler from year 3000 warns world leaders about imminent dinosaur invasion!",
        "Breaking: Major tech company announces plans to replace all human breathing with wireless oxygen!",
    ]
    train_labels = [0] * 8 + [1] * 8

    # Held-out Out-Of-Domain test set to demonstrate baseline failure on nuanced/paraphrased claims
    test_texts = [
        "The aerospace agency confirmed the launch of a lunar reconnaissance satellite next month.",  # Real (0)
        "Agricultural scientists reported that soil conservation techniques improved crop yield by twelve percent.",  # Real (0)
        "New study links Mediterranean diet with reduced risk of cardiovascular illness in adults.",  # Real (0)
        "Local transport authorities updated bus schedules for the downtown business district.",  # Real (0)
        "Doctors recommend avoiding raw dairy products due to potential bacterial contamination risks.",  # Real (0)
        "Secret military aircraft photographed creating artificial clouds to control global weather patterns.",  # Fake (1)
        "Celebrity politician arrested in top-secret tribunal and replaced with synthetic clone.",  # Fake (1)
        "Ancient scroll found in cave predicts massive asteroid impact scheduled for this Friday.",  # Fake (1)
        "Miracle magnetic bracelet permanently cures chronic diabetes and arthritis without medicine.",  # Fake (1)
        "Leaked documents reveal world governments plan to outlaw physical currency starting tomorrow.",  # Fake (1)
    ]
    test_labels = [0] * 5 + [1] * 5

    return DatasetSplit(texts=train_texts, labels=train_labels), DatasetSplit(texts=test_texts, labels=test_labels)
