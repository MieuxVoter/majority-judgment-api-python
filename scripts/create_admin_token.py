import tap
from app.auth import create_admin_token


class Arguments(tap.Tap):
    ref: str
    secret: str


def main(args: Arguments) -> None:
    print(create_admin_token(args.ref))


if __name__ == "__main__":
    args = Arguments().parse_args()
    main(args)
