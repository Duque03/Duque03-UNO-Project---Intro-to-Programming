"""The cosmetics drawings: every item can be drawn in every direction, and items look different."""

from arcade import bots, catalog
from arcade.art import sprites

LOOK = ("#e0b088", "#2b3a67")


def _sprite(hair=None, shirt=None, direction="down", t=0):
    return sprites.sprite(*LOOK, hair, shirt, direction, 0, t)


def test_every_hair_and_shirt_style_in_the_catalogue_can_be_drawn():
    for item in catalog.by_slot("hair"):
        assert item["spec"]["style"] in sprites.HAIR_STYLES, item["name"]
    for item in catalog.by_slot("shirt"):
        assert item["spec"]["style"] in sprites.SHIRT_STYLES, item["name"]
    for item in catalog.by_slot("hair") + catalog.by_slot("shirt"):
        hair = item["id"] if item["slot"] == "hair" else None
        shirt = item["id"] if item["slot"] == "shirt" else None
        for direction in ("down", "up", "left", "right"):
            assert _sprite(hair, shirt, direction).size == (sprites.SPR_W, sprites.SPR_H + 1)


def test_items_of_a_tab_all_look_different():
    for slot in ("hair", "shirt"):
        pictures = set()
        for item in catalog.by_slot(slot):
            hair = item["id"] if slot == "hair" else None
            shirt = item["id"] if slot == "shirt" else None
            front, back = _sprite(hair, shirt, "down"), _sprite(hair, shirt, "up")
            pictures.add(front.tobytes() + back.tobytes())
        assert len(pictures) == 26, slot


def test_kits_have_their_number_on_the_back_only():
    kit = next(i for i in catalog.by_slot("shirt") if i["spec"].get("num"))
    plain = dict(kit["spec"], num=None)
    assert sprites._number_pixel(kit["spec"]["num"], 7, 13) or sprites._number_pixel(kit["spec"]["num"], 5, 13)
    back = [sprites._shirt_colour(kit["spec"], x, y, 0, "back") for x in range(4, 12) for y in range(11, 16)]
    back_plain = [sprites._shirt_colour(plain, x, y, 0, "back") for x in range(4, 12) for y in range(11, 16)]
    front = [sprites._shirt_colour(kit["spec"], x, y, 0, "front") for x in range(4, 12) for y in range(11, 16)]
    front_plain = [sprites._shirt_colour(plain, x, y, 0, "front") for x in range(4, 12) for y in range(11, 16)]
    assert back != back_plain
    assert front == front_plain


def test_animated_items_change_over_time():
    galaxy = catalog.by_slot("hair", "legendary")[0]["id"]
    gold = catalog.by_slot("shirt", "legendary")[0]["id"]
    assert _sprite(galaxy, None, t=0).tobytes() != _sprite(galaxy, None, t=1).tobytes()
    assert _sprite(None, gold, t=0).tobytes() != _sprite(None, gold, t=1).tobytes()


def test_every_name_tag_can_be_drawn_with_a_long_name():
    from PIL import Image
    for item in catalog.by_slot("name"):
        img = Image.new("RGB", (400, 120))
        x0, y0, x1, y1 = sprites.draw_name_tag(img, 200, 90, "ABCDEFGHIJ", item["spec"])
        assert 0 < x0 < x1 < 400 and 0 < y0 < y1 <= 90, item["name"]


def test_bots_wear_items_that_exist():
    for bot in bots.BOTS + [bots.SHOPKEEPER]:
        for slot in ("hair", "shirt"):
            assert catalog.get(bot[slot])["slot"] == slot
        if "tag" in bot:
            assert catalog.get(bot["tag"])["slot"] == "name"
    looks = {bots.look(bot) for bot in bots.BOTS}
    assert len(looks) == len(bots.BOTS)


def test_showcase_shows_three_views_and_the_tag():
    img = sprites.showcase((*LOOK, "hair_c01", "shirt_c01"), "MIGUEL", "name_l01")
    assert img.width > 3 * sprites.SPR_W * 6 and img.height > sprites.SPR_H * 6
