def test_health_and_readiness(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ok"}


def test_signup_login_and_current_user(client):
    signup = client.post(
        "/signup",
        json={
            "firstName": "Demo",
            "lastName": "User",
            "email": "demo@example.com",
            "phone": "123456",
            "password": "strong-password",
        },
    )
    assert signup.status_code == 201

    login = client.post("/login", json={"email": "demo@example.com", "password": "strong-password"})
    assert login.status_code == 200
    token = login.json()["token"]

    current = client.get("/login", headers={"Authorization": token})
    assert current.status_code == 200
    assert current.json()["email"] == "demo@example.com"
    assert "password" not in current.json()


def test_duplicate_email_and_invalid_login(client):
    payload = {
        "firstName": "Demo",
        "lastName": "User",
        "email": "demo@example.com",
        "phone": "123456",
        "password": "strong-password",
    }
    assert client.post("/signup", json=payload).status_code == 201
    assert client.post("/signup", json=payload).status_code == 409
    assert (
        client.post("/login", json={"email": payload["email"], "password": "wrong"}).status_code
        == 401
    )


def test_public_pet_list_is_empty(client):
    response = client.get("/pet")
    assert response.status_code == 200
    assert response.json() == []
