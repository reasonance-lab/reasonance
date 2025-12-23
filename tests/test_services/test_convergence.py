"""Tests for convergence detection."""

import pytest
from llm_convergence.llm_convergence.services.convergence import ConvergenceDetector
from llm_convergence.llm_convergence.domain.models import Response, Round
from llm_convergence.llm_convergence.domain.enums import LLMProvider, ConvergenceStatus


def test_evaluate_first_round():
    """Test that first round is always pending."""
    round1 = Round(
        round_number=1,
        claude_response=Response(provider=LLMProvider.ANTHROPIC, content="Test"),
        openai_response=Response(provider=LLMProvider.OPENAI, content="Test")
    )

    status = ConvergenceDetector.evaluate_round(round1)
    assert status == ConvergenceStatus.PENDING


def test_evaluate_both_converged():
    """Test when both LLMs declare convergence."""
    round2 = Round(
        round_number=2,
        claude_response=Response(provider=LLMProvider.ANTHROPIC, content="Response"),
        openai_response=Response(provider=LLMProvider.OPENAI, content="Response"),
        claude_critique=Response(
            provider=LLMProvider.ANTHROPIC,
            content="I agree. CONVERGENCE DECLARED",
            is_critique=True,
            declares_convergence=True
        ),
        openai_critique=Response(
            provider=LLMProvider.OPENAI,
            content="We converged. CONVERGENCE DECLARED",
            is_critique=True,
            declares_convergence=True
        )
    )

    status = ConvergenceDetector.evaluate_round(round2)
    assert status == ConvergenceStatus.CONVERGED


def test_evaluate_diverged():
    """Test when only one LLM declares convergence."""
    round2 = Round(
        round_number=2,
        claude_response=Response(provider=LLMProvider.ANTHROPIC, content="Response"),
        openai_response=Response(provider=LLMProvider.OPENAI, content="Response"),
        claude_critique=Response(
            provider=LLMProvider.ANTHROPIC,
            content="I agree. CONVERGENCE DECLARED",
            is_critique=True,
            declares_convergence=True
        ),
        openai_critique=Response(
            provider=LLMProvider.OPENAI,
            content="I disagree with this approach",
            is_critique=True,
            declares_convergence=False
        )
    )

    status = ConvergenceDetector.evaluate_round(round2)
    assert status == ConvergenceStatus.DIVERGED


def test_check_agreement_signals():
    """Test detection of agreement signals in responses."""
    response_agree = Response(
        provider=LLMProvider.ANTHROPIC,
        content="I agree with this conclusion"
    )

    response_disagree = Response(
        provider=LLMProvider.OPENAI,
        content="This is incorrect"
    )

    assert ConvergenceDetector.check_agreement_signals(response_agree) is True
    assert ConvergenceDetector.check_agreement_signals(response_disagree) is False
