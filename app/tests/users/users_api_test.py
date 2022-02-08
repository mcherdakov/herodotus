import pytest
from fastapi import status

from app.tests.conftest import AuthClient
from app.users.models import User


@pytest.mark.anyio
async def test_me(auth_client: AuthClient, user: User):
    response = await auth_client.get("/users/me/", user=user)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["username"] == user.username
    assert data["uuid"] == str(user.uuid)
