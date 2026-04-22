from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(user_id: int) -> dict[str, str]:
    return {"x-user-id": str(user_id)}


def _good_content() -> str:
    words = " ".join(["seo"] * 320)
    return f"# SEO Workflow Guide\n\n## Planning\n\n{words}\n\nReference: https://example.com/ref"


def test_complete_seo_platform_flow() -> None:
    client.post("/_test/reset")

    admin = client.post("/users", json={"name": "Admin", "role": "admin"})
    seo_manager = client.post("/users", json={"name": "SEO", "role": "seo_manager"}, headers=_headers(1))
    assert admin.status_code == 201
    assert seo_manager.status_code == 201

    site_resp = client.post(
        "/sites",
        json={
            "name": "Global Site",
            "domain": "example.com",
            "default_language": "en",
            "supported_languages": ["en", "fr"],
        },
        headers=_headers(1),
    )
    assert site_resp.status_code == 201
    site_id = site_resp.json()["id"]

    user_author = client.post("/users", json={"name": "Alice", "role": "author"}, headers=_headers(1))
    user_editor = client.post("/users", json={"name": "Eve", "role": "editor"}, headers=_headers(1))
    user_reviewer = client.post("/users", json={"name": "Rob", "role": "reviewer"}, headers=_headers(1))
    user_publisher = client.post("/users", json={"name": "Pam", "role": "publisher"}, headers=_headers(1))
    assert user_author.status_code == 201
    assert user_editor.status_code == 201
    assert user_reviewer.status_code == 201
    assert user_publisher.status_code == 201

    author_id = user_author.json()["id"]
    editor_id = user_editor.json()["id"]
    reviewer_id = user_reviewer.json()["id"]
    publisher_id = user_publisher.json()["id"]

    keyword_resp = client.post(
        "/keywords",
        json={
            "site_id": site_id,
            "language": "en",
            "keyword": "seo content workflow",
            "intent": "informational",
            "search_volume": 2600,
            "difficulty": 42,
            "priority": 8,
            "cluster": "workflow",
        },
        headers=_headers(2),
    )
    assert keyword_resp.status_code == 201
    keyword_id = keyword_resp.json()["id"]

    article_resp = client.post(
        "/articles",
        json={
            "site_id": site_id,
            "language": "en",
            "title": "How to Build a Strict SEO Content Workflow That Scales",
            "slug": "strict-seo-content-workflow",
            "content": _good_content(),
            "author": "Alice",
            "author_id": author_id,
            "assignee_id": editor_id,
            "primary_keyword_id": keyword_id,
            "primary_keyword": "seo content workflow",
            "secondary_keywords": ["seo workflow", "content operations"],
        },
        headers=_headers(author_id),
    )
    assert article_resp.status_code == 201
    article_id = article_resp.json()["id"]
    assert article_resp.json()["status"] == "writing"

    quality_resp = client.post(
        f"/articles/{article_id}/quality-check",
        headers=_headers(editor_id),
    )
    assert quality_resp.status_code == 200
    quality_data = quality_resp.json()
    assert quality_data["hard_gate_passed"] is True
    assert quality_data["score"] >= 85

    submit_resp = client.post(f"/articles/{article_id}/submit-review", headers=_headers(editor_id))
    assert submit_resp.status_code == 200
    assert submit_resp.json()["new_status"] == "pending_review"

    seo_review_resp = client.post(
        f"/articles/{article_id}/review",
        json={"review_step": "seo", "approved": True},
        headers=_headers(reviewer_id),
    )
    assert seo_review_resp.status_code == 200
    assert seo_review_resp.json()["new_status"] == "pending_review"

    approve_resp = client.post(
        f"/articles/{article_id}/review",
        json={"review_step": "editorial", "approved": True},
        headers=_headers(reviewer_id),
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["new_status"] == "ready_to_publish"

    publish_resp = client.post(f"/articles/{article_id}/publish", headers=_headers(publisher_id))
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"
    assert publish_resp.json()["published_url"] == "https://example.com/strict-seo-content-workflow"

    index_1 = client.post(
        f"/articles/{article_id}/indexing-check",
        json={"day_offset": 3},
        headers=_headers(2),
    )
    assert index_1.status_code == 200
    assert index_1.json()["status"] == "indexed"

    details_resp = client.get(f"/articles/{article_id}", headers=_headers(2))
    assert details_resp.status_code == 200
    assert details_resp.json()["status"] == "indexed"
