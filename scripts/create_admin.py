import getpass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import User


def main():
    app = create_app()
    with app.app_context():
        email = input("E-mail: ").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=input("Nome: ").strip(), email=email, city="Sao Paulo", state="SP")
            user.set_password(getpass.getpass("Senha: "))
            db.session.add(user)
        user.is_admin = True
        db.session.commit()
        print(f"{email} agora e administrador.")


if __name__ == "__main__":
    main()
