import sqlite3
from types import SimpleNamespace

from data import db_bootstrapper
from data.repositories.lotto_repository import LottoRepository


DRAW = {
    "draw_no": 2,
    "numbers": [9, 13, 21, 25, 32, 42],
    "bonus_no": 2,
    "date": "2002-12-14",
    "total_sales_amount": 4904274000,
    "divisions": [
        {"prize": 2002006800, "winners": 1},
        {"prize": 94866800, "winners": 2},
        {"prize": 1842000, "winners": 103},
        {"prize": 100800, "winners": 3763},
        {"prize": 10000, "winners": 55480},
    ],
}


def test_repository_batch_maps_new_sales_and_divisions(tmp_path, monkeypatch):
    db_path = tmp_path / "lotto.db"
    monkeypatch.setattr(LottoRepository, "_get_db_path", staticmethod(lambda: str(db_path)))

    LottoRepository.save_draws_batch([DRAW])

    with sqlite3.connect(db_path) as conn:
        draw = conn.execute(
            "SELECT tot_sellamnt, first_accumamnt, first_przwner_co, first_winamnt, "
            "fifth_accumamnt, fifth_przwner_co, fifth_winamnt FROM lotto_draws"
        ).fetchone()
        history = conn.execute(
            "SELECT totSellamnt, secondAccumamnt, secondPrzwnerCo, secondWinamnt FROM lotto_history"
        ).fetchone()

    assert draw == (4904274000, 2002006800, 1, 2002006800, 554800000, 55480, 10000)
    assert history == (4904274000, 189733600, 2, 94866800)


def test_bootstrap_maps_new_sales_and_divisions(tmp_path, monkeypatch):
    monkeypatch.setattr(
        db_bootstrapper.requests,
        "get",
        lambda *args, **kwargs: SimpleNamespace(status_code=200, json=lambda: [DRAW]),
    )
    db_path = tmp_path / "bootstrap.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE lotto_history (drwNo INTEGER PRIMARY KEY, drwNoDate TEXT, "
            "drwtNo1 INTEGER, drwtNo2 INTEGER, drwtNo3 INTEGER, drwtNo4 INTEGER, "
            "drwtNo5 INTEGER, drwtNo6 INTEGER, bnusNo INTEGER)"
        )

    db_bootstrapper.DBBootstrapper._bootstrap_lotto_master_db(str(db_path))

    with sqlite3.connect(db_path) as conn:
        draw = conn.execute(
            "SELECT tot_sellamnt, first_accumamnt, first_przwner_co, first_winamnt FROM lotto_draws"
        ).fetchone()
        history = conn.execute(
            "SELECT totSellamnt, fifthAccumamnt, fifthPrzwnerCo, fifthWinamnt FROM lotto_history"
        ).fetchone()

    assert draw == (4904274000, 2002006800, 1, 2002006800)
    assert history == (4904274000, 554800000, 55480, 10000)


def test_repository_migrates_legacy_history_before_batch_insert(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(LottoRepository, "_get_db_path", staticmethod(lambda: str(db_path)))
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE lotto_history (drwNo INTEGER PRIMARY KEY, drwNoDate TEXT, "
            "drwtNo1 INTEGER, drwtNo2 INTEGER, drwtNo3 INTEGER, drwtNo4 INTEGER, "
            "drwtNo5 INTEGER, drwtNo6 INTEGER, bnusNo INTEGER)"
        )

    LottoRepository.save_draws_batch([DRAW])

    with sqlite3.connect(db_path) as conn:
        history = conn.execute(
            "SELECT totSellamnt, firstAccumamnt, firstPrzwnerCo, firstWinamnt, "
            "fifthAccumamnt, fifthPrzwnerCo, fifthWinamnt FROM lotto_history"
        ).fetchone()

    assert history == (4904274000, 2002006800, 1, 2002006800, 554800000, 55480, 10000)
