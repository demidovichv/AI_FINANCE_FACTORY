from agents.shared_models import Offer


def test_offer_validation():
    offer = Offer(
        id="offer_alfa_det",
        name="Test Card",
        offer_url="https://example.com",
        status="active"
    )

    assert offer.id == "offer_alfa_det"
    assert offer.status == "active"