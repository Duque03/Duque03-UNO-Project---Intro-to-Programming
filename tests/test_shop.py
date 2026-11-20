"""The store and the wardrobe picture (arcade/art/shop.py): everything is a click on the picture."""
from arcade import catalog, player
from arcade.art import shop, sprites
from arcade.config import RARITIES, SLOTS

LOOK = player.look(player.new_player("MIGUEL"))


def _view(slot="hair", actions=(), chosen=None):
    sections = [(rarity, [{"item": item, "picture": shop.tile_picture(item["id"], LOOK, "ABCDEFGHIJ"),
                           "badge": str(item["price"]), "kind": "price"} for item in catalog.by_slot(slot, rarity)])
                for rarity in RARITIES]
    return {"title": "STORE", "coins": 10, "slot": slot, "sections": sections, "chosen": chosen,
            "preview": sprites.showcase(LOOK, "MIGUEL", None, scale=4), "info": None, "actions": list(actions)}


def test_every_item_tab_and_back_can_be_clicked():
    for slot in SLOTS:
        _, regions = shop.shop_picture(_view(slot))
        actions = [action for _, action in regions]
        assert [a for a in actions if a[0] == "tab"] == [("tab", s) for s in SLOTS]
        assert ("back",) in actions
        assert sorted(a[1] for a in actions if a[0] == "item") == sorted(i["id"] for i in catalog.by_slot(slot))


def test_tiles_do_not_overlap_and_stay_on_the_picture():
    for slot in SLOTS:
        _, regions = shop.shop_picture(_view(slot))
        boxes = [box for box, action in regions if action[0] == "item"]
        for i, (l1, t1, r1, b1) in enumerate(boxes):
            assert 0 <= l1 and r1 <= shop.RIGHT_X and b1 <= 540
            for l2, t2, r2, b2 in boxes[i + 1:]:
                assert r1 <= l2 or r2 <= l1 or b1 <= t2 or b2 <= t1


def test_only_an_action_that_can_be_done_is_clickable():
    _, regions = shop.shop_picture(_view(actions=[("BUY FOR 100", "buy", False)]))
    assert ("buy",) not in [action for _, action in regions]
    _, regions = shop.shop_picture(_view(actions=[("WEAR IT", "wear", True)]))
    assert ("wear",) in [action for _, action in regions]


def test_the_longest_name_fits_in_a_name_tag_tile():
    for item in catalog.by_slot("name"):
        picture = shop.tile_picture(item["id"], LOOK, "ABCDEFGHIJ")  # the whole tag (effects too), cropped to it
        assert picture.width <= shop.tile_width(item) - 12 and picture.height <= 86, item["id"]


def test_hair_and_shirt_tiles_show_only_the_item_not_the_player():
    from arcade.art.pixel import rgb
    skin = rgb(LOOK[0])
    for slot in ("hair", "shirt"):
        for item in catalog.by_slot(slot):
            picture = shop.tile_picture(item["id"], LOOK, "MIGUEL").convert("RGBA")
            colours = {pixel[:3] for pixel in picture.get_flattened_data() if pixel[3]}
            assert skin not in colours, item["id"]  # no face, no hands: only the item
            assert picture.width <= shop.tile_width(item) - 12 and picture.height <= 86, item["id"]


def test_a_shirt_on_its_hanger_uses_the_shirt_colour():
    from arcade.art import sprites
    from arcade.art.pixel import rgb
    item = catalog.by_slot("shirt", "common")[0]
    colours = {pixel[:3] for pixel in sprites.shirt_item(item["id"]).get_flattened_data() if pixel[3]}
    assert rgb(item["spec"]["c1"]) in colours
