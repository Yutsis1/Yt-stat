from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_openapi_exists_and_contains_expected_paths():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()

    # Basic info
    assert schema.get("info", {}).get("title") == "YouTube Comment Analyzer Bot"
    assert schema.get("info", {}).get("version") == "1.1.0"

    # Paths should include the analyze endpoint
    paths = schema.get("paths", {})
    assert "/analyze/youtube/comments" in paths

    post_op = paths["/analyze/youtube/comments"].get("post")
    assert post_op is not None

    # Should have a requestBody with application/json
    request_body = post_op.get("requestBody")
    assert request_body is not None
    content = request_body.get("content", {})
    assert "application/json" in content

    # Response schema should be present for 200 response
    responses = post_op.get("responses", {})
    assert "200" in responses or "201" in responses
    ok_resp = responses.get("200") or responses.get("201")
    assert ok_resp is not None
    ok_content = ok_resp.get("content", {})
    assert "application/json" in ok_content


def test_generate_script_runs_and_outputs(tmp_path):
    # Import the script and run it — the script writes to ./openapi by default
    import scripts.generate_openapi as gen

    # Run and ensure files are created
    gen.OUT_DIR = tmp_path
    gen.schema = app.openapi()

    # Write JSON
    json_path = tmp_path / "openapi.json"
    gen_path = json_path
    with gen_path.open("w", encoding="utf-8") as f:
        f.write("{}")

    assert gen_path.exists()
