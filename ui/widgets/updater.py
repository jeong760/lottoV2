"""Compatibility shim for legacy updater imports."""

from data.updater import LOTTO_JSON_URL, get_draw_no, update_lotto_data

__all__ = ["LOTTO_JSON_URL", "get_draw_no", "update_lotto_data"]


if __name__ == "__main__":
    update_lotto_data()
