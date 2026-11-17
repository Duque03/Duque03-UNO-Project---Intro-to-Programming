import pytest

from arcade import catalog
from arcade.config import PRICES
from arcade.logic import store
from arcade.logic.store import StoreError


def test_catalogue_has_10_common_3_rare_1_legendary_per_tab():
    for slot in ("hair", "shirt", "name"):
        assert len(catalog.by_slot(slot, "common")) == 10
        assert len(catalog.by_slot(slot, "rare")) == 3
        assert len(catalog.by_slot(slot, "legendary")) == 1


def test_item_ids_and_names_are_unique_and_prices_follow_rarity():
    ids = [item["id"] for item in catalog.ITEMS]
    assert len(ids) == len(set(ids)) == 42
    for slot in ("hair", "shirt", "name"):
        names = [item["name"] for item in catalog.by_slot(slot)]
        assert len(names) == len(set(names))
    assert all(item["price"] == PRICES[item["rarity"]] for item in catalog.ITEMS)
    assert PRICES == {"common": 20, "rare": 100, "legendary": 500}


# ---- accepted actions

def test_buying_takes_coins_and_adds_the_item(player):
    player["coins"] = 25
    store.buy(player, "shirt_c01")
    assert player["coins"] == 5
    assert player["owned"] == ["shirt_c01"]


def test_equipping_an_owned_item_wears_it(player):
    player["coins"] = 20
    store.buy(player, "hair_c01")
    store.equip(player, "hair_c01")
    assert player["equipped"]["hair"] == "hair_c01"


def test_equipping_replaces_the_item_in_the_same_slot_only(player):
    player["owned"] = ["hair_c01", "hair_c02", "shirt_c01"]
    store.equip(player, "hair_c01")
    store.equip(player, "shirt_c01")
    store.equip(player, "hair_c02")
    assert player["equipped"] == {"hair": "hair_c02", "shirt": "shirt_c01", "name": None}


def test_unequip_goes_back_to_the_default_but_keeps_the_item(player):
    player["owned"] = ["name_l01"]
    store.equip(player, "name_l01")
    store.unequip(player, "name")
    assert player["equipped"]["name"] is None
    assert "name_l01" in player["owned"]
    assert catalog.spec_for("name", None) == catalog.DEFAULTS["name"]


def test_wardrobe_only_lists_owned_items(player):
    player["owned"] = ["hair_c03", "shirt_r01"]
    assert [i["id"] for i in store.owned_items(player, "hair")] == ["hair_c03"]
    assert store.owned_items(player, "name") == []


# ---- rejected actions

def test_buying_without_enough_coins_is_rejected_and_nothing_changes(player):
    player["coins"] = 19
    with pytest.raises(StoreError, match="Not enough coins"):
        store.buy(player, "shirt_c01")
    assert player["coins"] == 19 and player["owned"] == []


def test_buying_the_same_item_twice_is_rejected(player):
    player["coins"] = 100
    store.buy(player, "shirt_c01")
    with pytest.raises(StoreError):
        store.buy(player, "shirt_c01")
    assert player["coins"] == 80 and player["owned"] == ["shirt_c01"]


def test_buying_an_unknown_item_is_rejected(player):
    player["coins"] = 1000
    with pytest.raises(StoreError):
        store.buy(player, "shirt_x99")
    assert player["coins"] == 1000


def test_equipping_an_item_you_do_not_own_is_rejected(player):
    with pytest.raises(StoreError):
        store.equip(player, "hair_l01")
    assert player["equipped"]["hair"] is None


def test_unequipping_an_unknown_slot_is_rejected(player):
    with pytest.raises(StoreError):
        store.unequip(player, "shoes")


# ---- what each tile in the store shows (store.status)

def test_status_of_an_item_you_can_pay_for(player):
    player["coins"] = 20
    assert store.status(player, "shirt_c01") == "affordable"
    assert store.coins_missing(player, "shirt_c01") == 0


def test_status_of_an_item_you_cannot_pay_for(player):
    player["coins"] = 30
    assert store.status(player, "shirt_r01") == "too_expensive"
    assert store.coins_missing(player, "shirt_r01") == 70


def test_status_of_owned_and_worn_items(player):
    player["owned"] = ["hair_c01", "hair_c02"]
    store.equip(player, "hair_c02")
    assert store.status(player, "hair_c01") == "owned"
    assert store.status(player, "hair_c02") == "worn"
    store.unequip(player, "hair")
    assert store.status(player, "hair_c02") == "owned"


def test_status_of_an_unknown_item_is_refused(player):
    with pytest.raises(StoreError):
        store.status(player, "hair_x99")
    with pytest.raises(StoreError):
        store.coins_missing(player, "hair_x99")


def test_catalogue_names_are_original_designs():
    """No real clubs, brands or people in the item names (docs/game-design.md, store)."""
    banned = ("benfica", "porto", "sporting", "fortnite", "clash", "ronaldo", "messi", "nike", "adidas")
    for item in catalog.ITEMS:
        assert not any(word in item["name"].lower() for word in banned), item["name"]
