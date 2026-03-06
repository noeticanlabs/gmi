import json
from dataclasses import dataclass, asdict

@dataclass
class Receipt:
    """
    The immutable proof artifact for a single state transition.
    Must be re-checkable without re-running the inner loop.
    """
    step_index: int
    op_code: str
    x_hash_before: str
    x_hash_after: str
    v_before: float
    v_after: float
    sigma: float
    kappa: float
    budget_before: float
    budget_after: float
    is_composite: bool
    decision: str       # "ACCEPTED", "REJECTED", or "HALT"
    message: str

    def to_json(self) -> str:
        """Serializes the receipt for the cryptographic ledger log."""
        return json.dumps(asdict(self))
