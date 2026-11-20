"""The moving parts of the arcade (arcade/art/alive.py, table_room.py, room_layers.alive_patches)."""
from PIL import Image

from arcade import bots, catalog
from arcade.art import alive, room_layers, scenes, table_room
from arcade.config import BASE_H, BASE_W, SCREEN_H, SCREEN_W


def _check(patches):
    assert patches
    for p in patches:
        sizes = {frame.size for frame in p["frames"]}
        assert len(sizes) == 1 and len(p["frames"]) >= 2, p  # every picture of a loop has the same size
        (w, h), = sizes
        assert 0 <= p["x"] and p["x"] + w <= BASE_W and 0 <= p["y"] and p["y"] + h <= BASE_H
        assert p["fps"] > 0


def test_the_room_and_every_table_have_moving_parts_that_stay_on_the_picture():
    _check(room_layers.alive_patches())
    for kind in ("uno", "checkers", "connect4"):
        _check(table_room.patches(kind))
        assert table_room.backdrop(kind).size == (BASE_W, BASE_H)


def test_every_machine_game_loops():
    for game in range(6):
        frames = alive.screen_frames(game, "#58c4d8")
        assert len(frames) == alive.FRAMES and len({frame.tobytes() for frame in frames}) > 1


def test_a_part_of_the_wall_hidden_by_a_player_is_not_sent_and_an_empty_table_shows_it_all():
    opponents = [{"name": b["name"], "look": bots.look(b), "tag": catalog.spec_for("name", b["tag"])}
                 for b in bots.BOTS[:3]]
    table = scenes.table_scene("uno", opponents)
    assert table.info["alive"] == ("uno", 3)
    empty = scenes.empty_table_room("uno", 3)
    shown = table_room.visible_patches(table, empty, "uno")
    assert 0 < len(shown) < len(table_room.patches("uno"))  # the machine behind BARK is left out
    everything = table_room.visible_patches(empty, empty, "uno")
    assert len(everything) == len(table_room.patches("uno")) and all(p["mask"] is None for p in everything)
    dimmed = Image.new("RGB", (SCREEN_W, SCREEN_H))  # a dimmed table (the podium, a menu): nothing moves
    assert table_room.visible_patches(dimmed, empty, "uno") == []
