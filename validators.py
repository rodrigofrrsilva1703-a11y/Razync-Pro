from __future__ import annotations

import re


def only_digits(value: str | None) -> str:
    return re.sub(r"\D", "", str(value or ""))


def valid_email(value: str | None) -> bool:
    email = str(value or "").strip()
    if not email or len(email) > 254:
        return False
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))


def valid_competence(value: str | None) -> bool:
    return bool(re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", str(value or "").strip()))


def valid_cpf(value: str | None) -> bool:
    digits = only_digits(value)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    def digit(base: str, weight: int) -> str:
        total = sum(int(number) * factor for number, factor in zip(base, range(weight, 1, -1)))
        remainder = (total * 10) % 11
        return str(0 if remainder == 10 else remainder)

    first = digit(digits[:9], 10)
    second = digit(digits[:9] + first, 11)
    return digits[-2:] == first + second


def valid_cnpj(value: str | None) -> bool:
    digits = only_digits(value)
    if len(digits) != 14 or digits == digits[0] * 14:
        return False

    def check_digit(base: str, weights: tuple[int, ...]) -> str:
        total = sum(int(number) * weight for number, weight in zip(base, weights))
        remainder = total % 11
        return str(0 if remainder < 2 else 11 - remainder)

    first = check_digit(digits[:12], (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    second = check_digit(digits[:12] + first, (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    return digits[-2:] == first + second


def cpf_or_cnpj_status(value: str | None) -> tuple[bool, str]:
    digits = only_digits(value)
    if not digits:
        return True, ""
    if len(digits) == 11:
        return (True, "") if valid_cpf(digits) else (False, "CPF inválido.")
    if len(digits) == 14:
        return (True, "") if valid_cnpj(digits) else (False, "CNPJ inválido.")
    return False, "Informe um CPF com 11 dígitos ou CNPJ com 14 dígitos."
