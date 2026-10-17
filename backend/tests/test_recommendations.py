from app.routers.courses import _extract_interests, _rank_course_payloads


def test_data_interest_matches_data_course_with_rationale():
    courses = [
        {"id": "1", "code": "DATA-101", "title": "Data Analytics with Python", "description": "Analyze data and visualize findings.", "metadata": {}},
        {"id": "2", "code": "UX-101", "title": "UI/UX Design", "description": "User research and visual interfaces.", "metadata": {}},
    ]
    result = _rank_course_payloads(courses, "I enjoy statistics and finding patterns in data.")
    assert len(result) == 1
    assert result[0]["course"]["code"] == "DATA-101"
    assert result[0]["match_score"] > 0
    assert any("data analysis" in reason for reason in result[0]["rationale"])
    assert result[0]["score_type"] == "heuristic_similarity_not_admission_probability"


def test_no_identifiable_interest_does_not_guess_a_course():
    assert _extract_interests("I am not sure what I like yet.") == set()
    assert _rank_course_payloads([], "I am not sure what I like yet.") == []


def test_programming_interest_matches_web_development():
    courses = [
        {"id": "1", "code": "WEB-101", "title": "Full-Stack Web Development", "description": "Build websites and applications.", "metadata": {}},
    ]
    result = _rank_course_payloads(courses, "I want to build apps and learn programming.")
    assert result[0]["course"]["code"] == "WEB-101"
    assert "web development and programming" in result[0]["matched_interests"]
