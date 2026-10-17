from app.services.lead_scoring import extract_features, training_summary


def test_synthetic_dataset_has_both_labels_and_enough_examples():
    summary = training_summary()
    assert summary["examples"] >= 100
    assert summary["positive_labels"] > 0
    assert summary["negative_labels"] > 0
    assert summary["labels_are_synthetic"] is True


def test_feature_extraction_supports_marathi_demo_intent():
    features = extract_features("मला डेमो बुक करायचा आहे, पुढच्या महिन्यात प्रवेश घ्यायचा आहे.", "mr")
    assert features[4] == 1.0
    assert features[5] == 1.0
    assert features[12] == 1.0
