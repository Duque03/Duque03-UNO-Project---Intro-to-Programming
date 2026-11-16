"""A6: the extra room details are only decoration."""

from arcade import hubmap
from arcade.art import scenes
from arcade.config import BASE_H, BASE_W


def _pad_box():
    x, y = scenes.DANCE_PAD
    return x, y, x + scenes.DANCE_PAD_SIZE, y + scenes.DANCE_PAD_SIZE


def test_the_room_is_still_drawn_on_the_small_canvas():
    assert scenes._hub_background().size == (BASE_W, BASE_H)


def test_the_dance_pad_lies_on_walkable_floor():
    left, top, right, bottom = _pad_box()
    for x in range(left, right + 1, 4):
        for y in range(top, min(bottom, hubmap.WALK_AREA[3]) + 1, 4):
            assert not hubmap.blocked((x, y))  # you can walk over it


def test_the_dance_pad_covers_no_table_rug_or_place_to_stand():
    left, top, right, bottom = _pad_box()
    for key, spot in hubmap.SPOTS.items():
        sx, sy = spot["stand"]
        assert not (left <= sx <= right and top <= sy <= bottom), key
        if spot["kind"] == "table":
            cx, cy = spot["center"]
            rug = (cx - 40, cy - 14, cx + 40, cy + 28)
            assert right < rug[0] or left > rug[2] or bottom < rug[1] or top > rug[3], key
