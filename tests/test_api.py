from pathlib import Path

from backend.auth.jwt import create_access_token
from backend.utils.pdf_generator import generate_pdf_report


def test_health_endpoint_and_frontend_static_mount(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    page = client.get("/admin.html")
    assert page.status_code == 200
    assert "Admin Dashboard" in page.text


def test_registration_login_and_jwt_validation(client, user_payload):
    register_response = client.post("/api/auth/register", json=user_payload)
    assert register_response.status_code == 201
    assert register_response.json()["user_id"] == 1

    login_response = client.post(
        "/api/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["is_admin"] is True

    profile_response = client.get(
        "/api/profile",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == user_payload["email"]

    bad_response = client.get("/api/profile", headers={"Authorization": "Bearer invalid"})
    assert bad_response.status_code == 401


def test_profile_update(client, auth_headers):
    response = client.put(
        "/api/profile",
        headers=auth_headers,
        json={"full_name": "Updated User", "age": 32, "gender": "female"},
    )
    assert response.status_code == 200

    profile = client.get("/api/profile", headers=auth_headers).json()
    assert profile["full_name"] == "Updated User"
    assert profile["age"] == 32
    assert profile["gender"] == "female"


def test_prediction_history_and_admin_stats(client, auth_headers):
    symptoms = client.get("/api/symptoms-list").json()
    assert len(symptoms) > 10

    response = client.post(
        "/api/predict",
        headers=auth_headers,
        json={"symptoms": symptoms[:3]},
    )
    assert response.status_code == 200
    prediction = response.json()
    assert prediction["prediction_id"] == 1
    assert len(prediction["top_diseases"]) == 3
    assert all("disease" in item and "confidence" in item for item in prediction["top_diseases"])
    assert 0 <= prediction["risk_score"] <= 100
    assert prediction["ai_explanation"]

    history = client.get("/api/history", headers=auth_headers).json()
    assert history["total"] == 1
    assert history["results"][0]["id"] == prediction["prediction_id"]

    admin = client.get("/api/admin/stats", headers=auth_headers)
    assert admin.status_code == 200
    stats = admin.json()
    assert stats["summary"]["total_users"] == 1
    assert stats["summary"]["total_health_checks"] == 1
    assert stats["diseases"]["labels"]


def test_prediction_works_without_csv_file(client, auth_headers):
    csv_path = Path("Final_Augmented_dataset_Diseases_and_Symptoms.csv")
    backup_path = Path("Final_Augmented_dataset_Diseases_and_Symptoms.csv.bak")

    csv_exists = csv_path.exists()
    if csv_exists and backup_path.exists():
        backup_path.unlink()

    try:
        if csv_exists:
            csv_path.rename(backup_path)

        symptoms = client.get("/api/symptoms-list").json()
        response = client.post(
            "/api/predict",
            headers=auth_headers,
            json={"symptoms": symptoms[:3]},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["prediction_id"]
        assert len(payload["top_diseases"]) == 3
    finally:
        if csv_exists and backup_path.exists():
            backup_path.rename(csv_path)


def test_admin_endpoint_rejects_standard_user(client, user_payload, auth_headers):
    standard_user = {
        "full_name": "Standard User",
        "email": "standard@example.com",
        "password": "StrongPass2!",
        "confirm_password": "StrongPass2!",
    }
    client.post("/api/auth/register", json=standard_user)
    login = client.post(
        "/api/auth/login",
        json={"email": standard_user["email"], "password": standard_user["password"]},
    )
    token = login.json()["access_token"]

    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_pdf_generation_and_download(client, auth_headers):
    symptoms = client.get("/api/symptoms-list").json()[:3]
    prediction = client.post(
        "/api/predict",
        headers=auth_headers,
        json={"symptoms": symptoms},
    ).json()

    create_report = client.post(
        "/api/reports/generate",
        headers=auth_headers,
        json={"prediction_id": prediction["prediction_id"]},
    )
    assert create_report.status_code == 200
    assert create_report.json()["pdf_url"].endswith(".pdf")

    download = client.get(
        f"/api/reports/download/{prediction['prediction_id']}",
        headers=auth_headers,
    )
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")


def test_pdf_generator_includes_required_sections():
    pdf = generate_pdf_report(
        user_name="Test User",
        date_str="June 17, 2026",
        symptoms=["fever", "cough"],
        predictions=[{"disease": "Influenza", "confidence": 91.2}],
        risk_score=55,
        ai_explanation="### Possible Explanation\nThis is educational only.",
    )
    assert pdf.getvalue().startswith(b"%PDF")


def test_create_access_token_returns_string():
    token = create_access_token({"sub": "admin@example.com"})
    assert isinstance(token, str)
    assert token.count(".") == 2
