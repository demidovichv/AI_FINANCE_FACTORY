from agents.pipeline_manager import (
    PipelineManager
)


def test_create_and_load_state():

    state = PipelineManager.create_state(
        entity_id="offer_test",
        entity_type="offer"
    )

    loaded = PipelineManager.load_state(
        "offer_test"
    )

    assert (
        loaded.entity_id
        == "offer_test"
    )

    assert (
        loaded.entity_type
        == "offer"
    )

    assert (
        loaded.status
        == "pending"
    )