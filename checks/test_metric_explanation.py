"""Check the B2 article's finite-change criterion against direct DTI arithmetic."""
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def test_marginal_dti_condition_includes_epsilon_and_both_signs():
    explanation = (ROOT / 'docs/research/why-b2-scored-2778.md').read_text()
    assert '[(1−β)T + αF + βN + ε]' in explanation
    rng = random.Random(19)
    alpha, beta, eps = .2, .8, 1e-6
    wins = losses = 0
    for _ in range(5000):
        truth = rng.randint(1, 1000)
        true_old, true_new = rng.random() * truth, rng.random() * truth
        false_old, false_new = rng.random() * truth * 3, rng.random() * truth * 3
        old = true_old / ((1 - beta) * true_old + alpha * false_old + beta * truth + eps)
        new = true_new / ((1 - beta) * true_new + alpha * false_new + beta * truth + eps)
        criterion = ((1 - (1 - beta) * old) * (true_new - true_old)
                     > alpha * old * (false_new - false_old))
        assert criterion == (new > old)
        wins += new > old
        losses += new < old
    assert wins > 0 and losses > 0
