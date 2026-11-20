"""The UNO podium (arcade/art/podium.py): everyone in their place, and what can be clicked."""
from PIL import Image

from arcade import bots, catalog, player
from arcade.art import podium
from arcade.config import SCREEN_H, SCREEN_W

ME = player.new_player("MIGUEL")
EVERYONE = [{"name": "MIGUEL", "look": player.look(ME), "tag": ME["equipped"]["name"]}] + [
    {"name": b["name"], "look": bots.look(b), "tag": b["tag"]} for b in bots.BOTS[:3]]
TABLE = Image.new("RGB", (SCREEN_W, SCREEN_H), (40, 20, 30))


def test_every_player_stands_on_the_picture_whatever_the_number_of_players():
    for count in (2, 3, 4):
        pieces = podium.figures(EVERYONE[:count])
        assert len(pieces) == count
        for piece, (x, y) in pieces:
            assert 0 <= x and x + piece.width <= SCREEN_W and 0 <= y and y + piece.height <= SCREEN_H


def test_the_winner_stands_highest_and_second_left_of_third():
    pieces = podium.figures(EVERYONE)
    feet = [y + piece.height for piece, (x, y) in pieces]
    assert feet[0] < feet[1] < feet[2] <= feet[3]
    assert pieces[1][1][0] < pieces[0][1][0] < pieces[2][1][0]


def test_free_play_offers_continue_and_play_again_online_only_the_lobby():
    img, regions = podium.podium_picture(TABLE, "VICTORY!", EVERYONE, "MIGUEL", coins=45)
    assert img.size == (SCREEN_W, SCREEN_H)
    assert [action for _, action in regions] == [("continue",), ("again",)]
    _, regions = podium.podium_picture(TABLE, "2ND PLACE!", EVERYONE, "DEAN", footer="lobby")
    assert [action for _, action in regions] == [("lobby",)]


def test_a_name_tag_can_be_an_item_id_or_its_drawing():
    online = [dict(entry, tag=catalog.spec_for("name", entry["tag"])) for entry in EVERYONE]
    assert [p.size for p, _ in podium.figures(online)] == [p.size for p, _ in podium.figures(EVERYONE)]
