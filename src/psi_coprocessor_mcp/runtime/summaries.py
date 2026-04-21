"""Summary generation for PSI outputs."""

from __future__ import annotations

from ..models import PsiRunState, SummaryBundle


def generate_summary_bundle(
    run_state: PsiRunState,
    local_articulation_summary: dict[str, object],
    whole_field_impact_summary: list[str],
    strongest_tension: str,
    best_discriminator: str,
) -> SummaryBundle:
    visibility = run_state.state.O.title if run_state.state.O else "no explicit visibility event"
    lens = run_state.state.L.object_in_play or "task"
    friction_types = ", ".join(signal.friction_type.value for signal in run_state.state.F) or "none"
    transition = run_state.state.transition.decision.value
    compliance = run_state.state.compliance.status if run_state.state.compliance else "UNKNOWN"
    claim_note = ", ".join(
        f"{claim.provenance.value}/{claim.durability_class.value}"
        for claim in run_state.state.C[:2]
    ) or "no typed claims"
    expert_summary = (
        f"Visibility event: {visibility}. "
        f"Lens: {lens} @ {run_state.state.L.admissible_level or 'unspecified level'}. "
        f"Friction: {friction_types}. "
        f"Claim typing: {claim_note}. "
        f"Whole-field impact: {' | '.join(whole_field_impact_summary[:3])}. "
        f"Strongest live tension: {strongest_tension}. "
        f"Best discriminator: {best_discriminator}. "
        f"Transition: {transition}. "
        f"Compliance: {compliance}."
    )
    changed_surface = local_articulation_summary.get("changed_surface") or []
    plain_summary = (
        f"Something changed around {', '.join(changed_surface[:3]) or lens}. "
        f"The server thinks the main risk is {friction_types.lower()}. "
        f"The next move should test: {best_discriminator}. "
        f"Current transition recommendation: {transition}. "
        f"Compliance status: {compliance}."
    )
    compact_summary = f"{visibility} -> {transition}; compliance: {compliance}; discriminator: {best_discriminator}"
    return SummaryBundle(
        expert_summary=expert_summary,
        plain_summary=plain_summary,
        compact_summary=compact_summary,
    )
