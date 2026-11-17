"""The store grid: what Python sends to the browser and what it accepts back."""

from types import SimpleNamespace

from arcade import catalog, tiles

LOOK = ("#e0b088", "#2b3a67", None, None)


def test_a_tile_carries_its_state():
    item = catalog.get("shirt_r01")
    tile = tiles.tile(item, LOOK, "MIGUEL", picked=True, badge="100", badge_kind="poor")
    assert tile["id"] == "shirt_r01" and tile["picked"] and tile["kind"] == "poor" and not tile["worn"]
    assert tile["img"].startswith("data:image/png;base64,")
    assert not tile["wide"]
    assert tiles.tile(catalog.get("name_c01"), LOOK, "MIGUEL", picked=False, badge="20",
                      badge_kind="price")["wide"]


def test_a_whole_tab_stays_small_enough_to_send_quickly():
    for slot in ("hair", "shirt", "name"):
        section = [tiles.tile(item, LOOK, "ABCDEFGHIJ", picked=False, badge="20", badge_kind="price")
                   for item in catalog.by_slot(slot)]
        assert tiles.data_size([tiles.section("common", section)]) < 150_000, slot


def test_the_grid_accepts_only_real_item_ids(monkeypatch):
    answers = iter(["hair_c01", "hair_x99", "<script>", 42, None])
    monkeypatch.setattr(tiles, "_grid", lambda **kwargs: SimpleNamespace(pick=next(answers)))
    results = [tiles.grid([], key="test") for _ in range(5)]
    assert results == ["hair_c01", None, None, None, None]
