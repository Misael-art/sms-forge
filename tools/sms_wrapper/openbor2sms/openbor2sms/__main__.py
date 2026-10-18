"""python3 -m openbor2sms — CLI dispatch for the OpenBOR → SMS engine."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    from . import frontend, intake

    if argv and argv[0] in frontend.MODES:
        return frontend.main(argv)
    if "--self-check" in argv:
        status = intake.self_check()
        if status:
            return status
        return frontend.self_check()
    return intake.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
