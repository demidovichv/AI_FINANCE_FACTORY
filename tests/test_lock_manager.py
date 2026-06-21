from agents.lock_manager import LockManager


def test_lock_acquire_and_release():

    lm = LockManager(
        lock_dir="test_locks"
    )

    ok, _ = lm.acquire_lock(
        "offer",
        "offer_test",
        "run_1"
    )

    assert ok is True

    ok2, _ = lm.acquire_lock(
        "offer",
        "offer_test",
        "run_2"
    )

    assert ok2 is False

    released = lm.release_lock(
        "offer",
        "offer_test"
    )

    assert released is True