# Quantum Payments & Credits

Shared prepaid-credit contract. Grant credits only after verified idempotent payment events. Stripe and crypto must be provider adapters/webhooks; no crypto private keys or custody logic belong here. Production balances and ledger entries must be persisted transactionally. Reserve credits before generation and release on failure. Keep secrets out of Git.
