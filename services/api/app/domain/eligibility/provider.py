from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class CustomerContext:
    customer_id: str = "demo_user"


@dataclass(frozen=True)
class AvailableLimit:
    total_limit_paisa: int
    used_paisa: int
    available_paisa: int


@runtime_checkable
class EligibilityProvider(Protocol):
    async def get_available_limit(self, ctx: CustomerContext) -> AvailableLimit:
        ...


class StubEligibilityProvider:
    """
    Deterministic demo limit for the reference implementation.
    Total: ₹2,00,000 (20,000,000 paisa)
    Used:    ₹50,000 ( 5,000,000 paisa)
    Avail: ₹1,50,000 (15,000,000 paisa)
    """

    async def get_available_limit(self, ctx: CustomerContext) -> AvailableLimit:
        total = 20_000_000
        used = 5_000_000
        return AvailableLimit(
            total_limit_paisa=total,
            used_paisa=used,
            available_paisa=total - used,
        )


_eligibility_provider: EligibilityProvider = StubEligibilityProvider()


def get_eligibility_provider() -> EligibilityProvider:
    return _eligibility_provider
