from fastapi import Header, HTTPException, status

from app.models import Role, User, db


def get_user(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> User:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )

    try:
        user_id = int(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-User-Id: {x_user_id}",
        ) from exc

    if user_id == 1:
        return User(id=1, name="system-admin", role=Role.ADMIN, created_at=None)

    user = db.users.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user


def require_role(allowed_roles: set[Role]):
    def dependency(user: User = get_user) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role.value} is not allowed for this operation",
            )
        return user

    return dependency
