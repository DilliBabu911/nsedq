"""
NSEDQ Module 8: MUC Counter-Prompt Constructor (MUC-CPC)
Builds structured counter-prompts from solver proof trees.
"""
from .scv import format_proof_tree
from .cdl_grammar import CDLConstraint


# Simple CCRG (Conflict Resolution Graph) in-memory store
_ccrg = {}


STRATEGIES = [
    "Range bound widening: increase upper or decrease lower bound by 10-20%",
    "Conditional qualification: convert absolute RANGE to CONDITIONAL(domain -> RANGE)",
    "Cardinality relaxation: relax UNIQUE to allow limited duplicates via CONDITIONAL",
    "Semantic type narrowing: restrict to a specific ontology sub-class",
    "Constraint withdrawal: withdraw the constraint with lower CTS",
]


def build_counter_prompt(muc: list, profiles: dict,
                          iteration: int) -> str:
    """
    Build a structured counter-prompt for NCP re-invocation.
    """
    proof_text = format_proof_tree(muc, profiles)

    # Retrieve CCRG strategies for similar conflicts
    strategies = _retrieve_ccrg_strategies(muc)
    strategy_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(strategies))

    prompt = (
        f"=== CONSTRAINT CONFLICT — ITERATION {iteration} ===\n\n"
        f"{proof_text}\n\n"
        f"Ranked resolution strategies (from conflict history):\n"
        f"{strategy_text}\n\n"
        f"Instructions:\n"
        f"  - Revise or withdraw the constraint(s) identified above.\n"
        f"  - Produce a corrected CDL expression list.\n"
        f"  - Do NOT re-propose the same conflicting expressions.\n"
        f"  - Return ONLY a JSON array of CDL expression strings.\n"
    )
    return prompt


def _retrieve_ccrg_strategies(muc: list) -> list:
    """Retrieve ranked strategies. Simple: use all defaults for now."""
    # In a production system this uses cosine similarity over embeddings
    # For the experimental implementation: return ranked default strategies
    return STRATEGIES[:4]


def record_ccrg_outcome(muc_key: str, strategy_idx: int, success: bool):
    """Update CCRG strategy scores."""
    if muc_key not in _ccrg:
        _ccrg[muc_key] = [1.0] * len(STRATEGIES)
    if 0 <= strategy_idx < len(STRATEGIES):
        if success:
            _ccrg[muc_key][strategy_idx] = min(2.0, _ccrg[muc_key][strategy_idx] + 0.2)
        else:
            _ccrg[muc_key][strategy_idx] = max(0.1, _ccrg[muc_key][strategy_idx] - 0.1)
