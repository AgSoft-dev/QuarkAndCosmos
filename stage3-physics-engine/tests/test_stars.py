"""Distribution des étoiles par lancer de rayons (cf. engine/stars.py)."""
from engine.generator import make_level
from engine.stars import star_profile, target_shares


def test_targets_follow_truncated_gaussian():
    for d in (1, 2, 3):
        t = target_shares(d)
        assert 1 > t[1] > t[2] > t[3] > 0
    # σ diminue avec la difficulté : chaque palier se resserre
    for k in (1, 2, 3):
        assert target_shares(1)[k] > target_shares(2)[k] > target_shares(3)[k]


def test_three_star_window_narrows_with_difficulty():
    # tunnel : 300+ chemins distincts, la cible est atteignable à chaque
    # difficulté (cf. rapport `cli.py report`)
    shares = [star_profile(make_level("tunnel", d))["shares"] for d in (1, 2, 3)]
    assert shares[0]["3"] > shares[1]["3"] > shares[2]["3"]
    for d, s in zip((1, 2, 3), shares):
        assert abs(s["3"] - target_shares(d)[3]) <= 0.05
