from jose import jws
import tap


class Arguments(tap.Tap):
    ref: str
    secret: str


def create_admin_token(election_ref: str, secret: str) -> str:
    return jws.sign(
        {"admin": True, "election": election_ref},
        secret,
        algorithm="HS256",
    )


def main(args: Arguments) -> None:
    print(create_admin_token(args.ref, args.secret))


if __name__ == "__main__":
    args = Arguments().parse_args()
    main(args)
