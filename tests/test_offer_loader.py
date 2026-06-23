from agents.offer_loader import OfferLoader


def test_load_offer():

    offer = OfferLoader.load(
        "Obsidian/Offers/offer_alfa_kids.md"
    )

    assert offer.id == "offer_alfa_kids"
    assert offer.status == "active"
    assert offer.bank == "Альфа-Банк"