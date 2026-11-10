"""Separate strict bounded CLI for max-parity reports; retains the old CLI."""

from .__main__ import main as bounded_main
from .parity import analyze
from .parity_oracle import verify


def main():
    return bounded_main(
        analyze,
        verify,
        "buchilab-parity-v1",
        "Inspect finite total max-recurring-priority parity games",
    )


if __name__ == "__main__":
    raise SystemExit(main())
