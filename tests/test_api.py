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


def _create_admin(db):
    from app.models import User
    from app.security import create_access_token, hash_password

    admin = User(
        firstname="Admin",
        lastname="User",
        email="admin@example.com",
        phone="123456",
        password=hash_password("strong-password"),
        admin=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin, create_access_token(str(admin.id))


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


def test_save_and_unsave_pet(client, db):
    token = _signup_and_login(client, "saved@example.com")
    current = client.get("/login", headers={"Authorization": token}).json()
    pet_id = _create_pet(db)

    first_save = client.post(f"/pet/{pet_id}/save", json={}, headers={"Authorization": token})
    second_save = client.post(f"/pet/{pet_id}/save", json={}, headers={"Authorization": token})
    assert first_save.status_code == 200
    assert second_save.json()["id"] == first_save.json()["id"]

    unsave = client.delete(f"/pet/{first_save.json()['id']}/save", headers={"Authorization": token})
    collections = client.get(f"/pet/user/{current['id']}", headers={"Authorization": token})
    assert unsave.status_code == 200
    assert collections.json()["saved_pets"] == []


def test_only_owner_can_return_pet(client, db):
    owner_token = _signup_and_login(client, "return-owner@example.com")
    visitor_token = _signup_and_login(client, "return-visitor@example.com")
    pet_id = _create_pet(db)
    client.post(f"/pet/{pet_id}/foster", json={}, headers={"Authorization": owner_token})

    forbidden = client.post(f"/pet/{pet_id}/return", headers={"Authorization": visitor_token})
    returned = client.post(f"/pet/{pet_id}/return", headers={"Authorization": owner_token})

    assert forbidden.status_code == 403
    assert returned.status_code == 200
    assert returned.json()["adoption_status"] == "Available"
    assert returned.json()["taken_by_user_id"] is None


def test_user_can_update_own_profile_but_not_another_users(client):
    owner_token = _signup_and_login(client, "profile-owner@example.com")
    other_token = _signup_and_login(client, "profile-other@example.com")
    owner = client.get("/login", headers={"Authorization": owner_token}).json()

    update = client.put(
        f"/user/{owner['id']}",
        json={"firstname": "Updated", "bio": "Ready to adopt"},
        headers={"Authorization": owner_token},
    )
    forbidden = client.put(
        f"/user/{owner['id']}",
        json={"firstname": "Intruder"},
        headers={"Authorization": other_token},
    )
    updated = client.get(f"/user/{owner['id']}").json()

    assert update.status_code == 200
    assert forbidden.status_code == 403
    assert updated["firstname"] == "Updated"
    assert updated["bio"] == "Ready to adopt"


def test_profile_update_rejects_duplicate_email(client):
    first_token = _signup_and_login(client, "first@example.com")
    _signup_and_login(client, "second@example.com")
    first = client.get("/login", headers={"Authorization": first_token}).json()

    response = client.put(
        f"/user/{first['id']}",
        json={"email": "second@example.com"},
        headers={"Authorization": first_token},
    )

    assert response.status_code == 409


def test_admin_user_list_is_protected(client, db):
    regular_token = _signup_and_login(client, "regular@example.com")
    _, admin_token = _create_admin(db)

    assert client.get("/user").status_code == 401
    assert client.get("/user", headers={"Authorization": regular_token}).status_code == 403
    response = client.get("/user", headers={"Authorization": admin_token})
    assert response.status_code == 200
    assert {user["email"] for user in response.json()} == {
        "regular@example.com",
        "admin@example.com",
    }


def test_protected_pet_actions_require_login(client, db):
    pet_id = _create_pet(db)

    assert client.post(f"/pet/{pet_id}/adopt", json={}).status_code == 401
    assert client.post(f"/pet/{pet_id}/foster", json={}).status_code == 401
    assert client.post(f"/pet/{pet_id}/save", json={}).status_code == 401


def test_admin_can_add_and_edit_pet(client, db, monkeypatch):
    _, admin_token = _create_admin(db)

    async def fake_upload(_file):
        return "https://example.com/uploaded-pet.jpg"

    monkeypatch.setattr("app.routers.pets.upload_pet_image", fake_upload)
    fields = {
        "type": "Cat",
        "name": "Pixel",
        "adoption_status": "Available",
        "height": "28",
        "weight": "4.5",
        "color": "Black",
        "bio": "A curious cat",
        "hypoallergenic": "false",
        "dietary_restrictions": "None",
        "breed": "Domestic shorthair",
    }

    added = client.post(
        "/pet",
        data=fields,
        files={"picture": ("pixel.jpg", b"image", "image/jpeg")},
        headers={"Authorization": admin_token},
    )
    assert added.status_code == 201

    edited = client.put(
        f"/pet/{added.json()['id']}",
        data={**fields, "name": "Pixel Updated"},
        headers={"Authorization": admin_token},
    )
    assert edited.status_code == 200
    assert edited.json()["name"] == "Pixel Updated"
    assert edited.json()["picture"] == "https://example.com/uploaded-pet.jpg"


def test_full_user_response_includes_owned_pets(client, db):
    token = _signup_and_login(client, "full-user@example.com")
    current = client.get("/login", headers={"Authorization": token}).json()
    pet_id = _create_pet(db)
    client.post(f"/pet/{pet_id}/adopt", json={}, headers={"Authorization": token})

    response = client.get(f"/user/{current['id']}/full", headers={"Authorization": token})

    assert response.status_code == 200
    assert [pet["id"] for pet in response.json()["owned_pets"]] == [pet_id]
    assert "password" not in response.json()
