"""Distribution des étoiles par lancer de rayons (cf. engine/stars.py)."""
from engine.stars import target_shares


def test_targets_follow_truncated_gaussian():
    for d in (1, 2, 3):
        t = target_shares(d)
        assert 1 > t[1] > t[2] > t[3] > 0
    # σ diminue avec la difficulté : chaque palier se resserre
    for k in (1, 2, 3):
        assert target_shares(1)[k] > target_shares(2)[k] > target_shares(3)[k]
