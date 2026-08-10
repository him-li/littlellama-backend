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
            "confirmPassword": "strong-password",
        },
    )
    assert signup.status_code == 201

    signup_token = signup.json()["token"]
    current = client.get("/login", headers={"Authorization": signup_token})
    assert current.status_code == 200
    assert current.json()["email"] == "demo@example.com"

    login = client.post("/login", json={"email": "demo@example.com", "password": "strong-password"})
    assert login.status_code == 200
    token = login.json()["token"]

    logged_in = client.get("/login", headers={"Authorization": token})
    assert logged_in.status_code == 200
    assert logged_in.json()["email"] == "demo@example.com"
    assert "password" not in logged_in.json()


def test_duplicate_email_and_invalid_login(client):
    payload = {
        "firstName": "Demo",
        "lastName": "User",
        "email": "demo@example.com",
        "phone": "123456",
        "password": "strong-password",
        "confirmPassword": "strong-password",
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


def _signup_and_login(client, email):
    signup = client.post(
        "/signup",
        json={
            "firstName": "Demo",
            "lastName": "User",
            "email": email,
            "phone": "123456",
            "password": "strong-password",
            "confirmPassword": "strong-password",
        },
    )
    assert signup.status_code == 201
    login = client.post("/login", json={"email": email, "password": "strong-password"})
    assert login.status_code == 200
    return login.json()["token"]


def test_signup_rejects_mismatched_passwords(client):
    response = client.post(
        "/signup",
        json={
            "firstName": "Demo",
            "lastName": "User",
            "email": "mismatch@example.com",
            "phone": "123456",
            "password": "strong-password",
            "confirmPassword": "different-password",
        },
    )

    assert response.status_code == 422


def _create_pet(db, **overrides):
    from app.models import Pet

    fields = {
        "type": "Dog",
        "name": "Mochi",
        "adoption_status": "Available",
        "height": 42,
        "weight": 13,
        "color": "Cream",
        "bio": "A friendly demo dog",
        "hypoallergenic": False,
        "dietary_restrictions": "None",
        "breed": "Mixed",
        "picture": "https://example.com/mochi.jpg",
    }
    fields.update(overrides)
    pet = Pet(**fields)
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return str(pet.id)


def test_pet_details_are_public(client, db):
    pet_id = _create_pet(db)

    response = client.get(f"/pet/{pet_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Mochi"
    assert response.json()["taken_by_user_id"] is None


def test_only_fosterer_can_adopt_fostered_pet(client, db):
    fosterer_token = _signup_and_login(client, "fosterer@example.com")
    other_token = _signup_and_login(client, "other@example.com")
    pet_id = _create_pet(db)

    foster = client.post(
        f"/pet/{pet_id}/foster",
        json={},
        headers={"Authorization": fosterer_token},
    )
    assert foster.status_code == 200
    fosterer_id = foster.json()["taken_by_user_id"]

    takeover = client.post(
        f"/pet/{pet_id}/adopt",
        json={},
        headers={"Authorization": other_token},
    )
    assert takeover.status_code == 409

    adopt = client.post(
        f"/pet/{pet_id}/adopt",
        json={},
        headers={"Authorization": fosterer_token},
    )
    assert adopt.status_code == 200
    assert adopt.json()["adoption_status"] == "Adopted"
    assert adopt.json()["taken_by_user_id"] == fosterer_id


def test_owned_pet_cannot_be_fostered_or_reassigned(client, db):
    owner_token = _signup_and_login(client, "owner@example.com")
    other_token = _signup_and_login(client, "visitor@example.com")
    pet_id = _create_pet(db)

    adopt = client.post(f"/pet/{pet_id}/adopt", json={}, headers={"Authorization": owner_token})
    assert adopt.status_code == 200

    foster = client.post(f"/pet/{pet_id}/foster", json={}, headers={"Authorization": other_token})
    adopt_again = client.post(
        f"/pet/{pet_id}/adopt", json={}, headers={"Authorization": other_token}
    )

    assert foster.status_code == 409
    assert adopt_again.status_code == 409


def test_user_pet_collections_separate_owned_and_saved_pets(client, db):
    token = _signup_and_login(client, "collector@example.com")
    current = client.get("/login", headers={"Authorization": token}).json()
    owned_pet_id = _create_pet(db)
    saved_pet_id = _create_pet(db)

    adopt = client.post(f"/pet/{owned_pet_id}/adopt", json={}, headers={"Authorization": token})
    save = client.post(f"/pet/{saved_pet_id}/save", json={}, headers={"Authorization": token})
    assert adopt.status_code == 200
    assert save.status_code == 200

    response = client.get(f"/pet/user/{current['id']}", headers={"Authorization": token})

    assert response.status_code == 200
    assert [pet["id"] for pet in response.json()["owned_pets"]] == [owned_pet_id]
    assert [pet["id"] for pet in response.json()["saved_pets"]] == [saved_pet_id]


def test_pet_search_uses_independent_name_height_and_weight_filters(client, db):
    matching_id = _create_pet(db, name="Mochi One", height=42, weight=13)
    _create_pet(db, name="Mochi Two", height=42, weight=18)
    _create_pet(db, name="Pepper", height=42, weight=13)

    response = client.get("/pet", params={"name": "Mochi", "height": 42, "weight": 13})

    assert response.status_code == 200
    assert [pet["id"] for pet in response.json()] == [matching_id]


def test_pet_search_rejects_non_positive_measurements(client):
    assert client.get("/pet", params={"height": 0}).status_code == 422
    assert client.get("/pet", params={"weight": -1}).status_code == 422
