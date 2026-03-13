from backend.llm import parse_analysis_response


def test_parse_analysis_response_repairs_trailing_commas_and_prose():
    payload = {
        "content": [
            {
                "type": "text",
                "text": "Here is the result:\n```json\n{\n  \"title_zh\": \"t\",\n  \"summary_zh\": \"s\",\n  \"impact_scope\": \"scope\",\n  \"suggested_action\": \"act\",\n  \"urgency\": \"low\",\n  \"tags\": [\"k\"],\n  \"is_stable\": true,\n}\n```",
            }
        ]
    }
    parsed = parse_analysis_response(payload)
    assert parsed["title_zh"] == "t"


def test_parse_analysis_response_repairs_unterminated_string():
    payload = {
        "content": [
            {
                "type": "text",
                "text": "{\n  \"title_zh\": \"t\",\n  \"summary_zh\": \"s\",\n  \"impact_scope\": \"scope\",\n  \"suggested_action\": \"act\",\n  \"urgency\": \"low\",\n  \"tags\": [\"k\"],\n  \"is_stable\": true,\n  \"details_zh\": \"missing end\n",
            }
        ]
    }
    parsed = parse_analysis_response(payload)
    assert parsed["summary_zh"] == "s"
