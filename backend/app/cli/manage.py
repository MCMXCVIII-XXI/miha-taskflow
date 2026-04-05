import asyncio

import typer
from sqlalchemy import select

from app.core.security import get_password_hash
from app.db import db_helper
from app.models import User
from app.schemas.enum import GlobalUserRole

app = typer.Typer()


@app.command()
def create_admin(
    email: str = typer.Option(..., prompt=True, help="Enter the admin email"),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        help="Enter the admin password",
        confirmation_prompt=True,
    ),
) -> None:
    """
    Create an admin user

    Details:
        This command creates a new admin user with the specified email and password.
        If the user already exists, an error message is displayed and the command exits.

    Args:
        email (str): The admin email
        password (str): The admin password

    Returns:
        None
    """

    async def _create_admin() -> None:
        async with db_helper.get_session_ctx() as session:
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.first()
            if existing_user:
                typer.echo(f"Error: User with email {email} already exists", err=True)
                raise typer.Exit(1)

            username = email.split("@")[0]

            user = User(
                username=username,
                email=email,
                first_name="Admin",
                last_name="Admin",
                hashed_password=get_password_hash(password),
                role=GlobalUserRole.ADMIN,
            )
            session.add(user)
            await session.commit()

        typer.echo(f"Admin created successfully: {email}")

    asyncio.run(_create_admin())


if __name__ == "__main__":
    app()
