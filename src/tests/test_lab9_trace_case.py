"""Regression test for docs/trace_case.md: seeded_regression C-014@11 (FM-05 pre_deducted).

First wrong step: event `proposal {"amount_vnd": 120000}` right after `refund_history` -- the agent
subtracts the prior 30.000đ refund itself, the host subtracts it again, ledger ends at 90.000đ.
The test must FAIL on the buggy variant and PASS on `fixed`.
"""
import pytest

pytestmark = pytest.mark.student

CLAIM, SEED = "C-014", 11


def _grade(shape):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import ProposalMatchesQuote, ReplyAmountMatchesLedger, RefundAmountCorrect
    from lab9.trace_case import investigate

    case = investigate(shape, CLAIM, SEED)
    ctx = EvaluatorContext(name=f"{CLAIM}@{SEED}", inputs={}, metadata=None, expected_output=case["label"],
                           output=case["trial"], duration=0.0, _span_tree=None, attributes={}, metrics={})
    return case["trial"], {g.__name__: g().evaluate(ctx).value
                           for g in (RefundAmountCorrect, ProposalMatchesQuote, ReplyAmountMatchesLedger)}


def _first_wrong_step(events):
    """Index (1-based) of the first event whose amount departs from the quote."""
    quote = next(e["payload"]["amount_vnd"] for e in events if e.get("kind") == "quote")
    for i, e in enumerate(events, 1):
        if e.get("kind") == "proposal" and e["payload"]["amount_vnd"] != quote:
            return i, e
    return None, None


def test_lab9_trace_case_seeded_regression_is_caught():
    trial, verdict = _grade("seeded_regression")
    assert trial["snapshot"]["refund_vnd"] == 90000
    assert verdict == {"RefundAmountCorrect": False, "ProposalMatchesQuote": False, "ReplyAmountMatchesLedger": False}
    step, event = _first_wrong_step(trial["events"])
    assert event is not None and event["payload"]["amount_vnd"] == 120000
    assert trial["events"][step - 2]["kind"] == "refund_history"   # the deduction comes from the history lookup


def test_lab9_trace_case_fixed_passes():
    trial, verdict = _grade("fixed")
    assert trial["snapshot"]["refund_vnd"] == 120000
    assert all(verdict.values()), verdict
    assert _first_wrong_step(trial["events"]) == (None, None)
