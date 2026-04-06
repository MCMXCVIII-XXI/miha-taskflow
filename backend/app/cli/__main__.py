import typer

from app.cli import manage

app = typer.Typer()
app.add_typer(manage.app, name="manage")


if __name__ == "__main__":
    app()
