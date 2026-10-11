# Benefit-IQ

- Backend: `benefit-iq-be/src/benefit_iq`, FastAPI, application contracts, domain dataclasses, ClickHouse adapters. Frontend: Angular in `benefit-iq-fe`.
- Preserve existing working-tree changes. Do not replace architecture to match obsolete BigQuery documentation.
- Money uses Decimal; never aggregate different currencies or treat insurance coverage/visit counts as cash savings.
- Customer IDs must be authorized server-side. Catalogue reads differ from privileged portfolio operations.
- Never return fabricated analytics, model confidence, or claimed evaluation accuracy. Synthetic fixtures must be identified.
- Use UTC, explicit calculation timestamps and half-open benefit periods. Usage is scoped to customer, card, benefit and currency.
- Run backend tests with `.venv/Scripts/python -m pytest benefit-iq-be/tests`; frontend build with `npm.cmd run build` in `benefit-iq-fe`.
- Keep execution evidence and unresolved production gaps in `docs/IMPLEMENTATION_STATUS.md`.
