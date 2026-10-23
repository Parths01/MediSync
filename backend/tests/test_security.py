from pwdlib.hashers.bcrypt import BcryptHasher

from app.security import hash_password, verify_password_and_update


def test_new_password_hash_uses_current_argon2_hasher() -> None:
    hashed_password = hash_password("correct horse battery staple")

    valid, replacement = verify_password_and_update(
        "correct horse battery staple",
        hashed_password,
    )

    assert valid
    assert replacement is None
    assert hashed_password.startswith("$argon2")


def test_legacy_bcrypt_password_is_accepted_and_upgraded() -> None:
    legacy_hash = BcryptHasher().hash("legacy-password")

    valid, replacement = verify_password_and_update("legacy-password", legacy_hash)

    assert valid
    assert replacement is not None
    assert replacement.startswith("$argon2")
