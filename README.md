# Benefit-Underutilization Analytics

## Problem

Card issuers invest heavily in benefits such as travel credits, lounge access, and protection coverage, but typically lack a reliable way to measure how much of that value remains unclaimed.

At the same time, card members may be unaware of benefits they are already entitled to.

This creates two problems:

- Limited dollar-level visibility into benefit ROI for issuers
- Reduced perceived card value for members

The proposed system converts this invisible unused value into a measurable engagement opportunity.

---

## Solution

The system combines a **rules-based entitlement engine**, **unclaimed-value calculator**, **ML-based nudge engine**, and **member/issuer analytics surfaces**.

### End-to-end pipeline

```text
Transactions ───────┐
                    │
Entitlement Rules ──┼──> BigQuery
                    │       │
Redemption Logs ────┘       ▼
                     Entitlement Mapping
                             │
                             ▼
                    Unclaimed Value Engine
                             │
                             ▼
                      Nudge Threshold?
                       /            \
                     No              Yes
                     │                │
                     ▼                ▼
              Dashboard Only    XGBoost Scoring
                                      │
                                      ▼
                              Channel + Timing
                                      │
                                      ▼
                                  Nudge
```

---

## Key Capabilities

### 1. Entitlement Mapping

Maps each member to the benefits associated with their card product and evaluates transactions against benefit rules.

Examples include:

- Travel credits
- Lounge visits
- Protection coverage

The entitlement logic is designed to be **configuration-driven**, allowing rules to vary by card SKU.

### 2. Unclaimed Value Calculation

The valuation engine calculates the estimated dollar value of benefits that remain unused during a benefit cycle.

Example:

```text
Travel Credit      $150
Lounge Access      $120
Protection          $72
------------------------
Total Unclaimed    $342
```

### 3. Personalized Nudge Engine

Members with meaningful unclaimed value can be prioritized for engagement.

An **XGBoost propensity model** scores the likelihood of useful engagement, after which the system selects an appropriate channel and timing based on spending patterns.

### 4. Member Dashboard

The proposed member-facing dashboard surfaces:

- Total unclaimed benefit value
- Category-wise breakdown
- Benefits approaching expiration
- Personalized recommendations
- Clear redemption CTAs

### 5. Issuer Analytics

Issuer-side analytics provide visibility into:

- Benefit utilization
- Unclaimed value
- Redemption trends
- Nudge performance
- Portfolio-level recovery

---

## Architecture

```text
                    ┌─────────────────────┐
                    │ Transactions        │
                    ├─────────────────────┤
                    │ Entitlement Rules   │
                    ├─────────────────────┤
                    │ Redemption Logs     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      BigQuery       │
                    │  Raw + Curated Data │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌───────────┐   ┌─────────────┐   ┌────────────┐
        │   Rules   │   │  Valuation  │   │   Nudge    │
        │  Engine   │   │   Engine    │   │   Engine   │
        └─────┬─────┘   └──────┬──────┘   └─────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                       ┌──────────────┐
                       │   FastAPI    │
                       └──────┬───────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Angular Dashboard          Notifications
                 │
                 ▼
          Tableau Embedded
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Angular | Member-facing dashboard |
| Analytics | Tableau Embedded | Issuer-side analytics and reporting |
| Backend | Python, FastAPI | APIs for entitlement, valuation and nudge services |
| ML | scikit-learn, XGBoost | Matching, anomaly checks and propensity scoring |
| Data Processing | Pandas, NumPy, PySpark | Analytical and batch computation |
| Data Warehouse | BigQuery | Transaction and entitlement data |
| Caching | Redis | Read-heavy dashboard metrics |
| Configuration | YAML | Versioned, config-driven entitlement rules |

---

## Core Workflow

### Step 1 — Load Entitlements

Benefit rules are configured for each card SKU.

```text
Card SKU
   ↓
Benefit Rules
   ↓
Eligible Benefits
```

### Step 2 — Match Transactions

Transactions are evaluated using merchant and MCC-based rules.

```text
Transaction
   ↓
Merchant / MCC
   ↓
Eligibility Rule
   ↓
Benefit Match
```

### Step 3 — Calculate Unclaimed Value

The system evaluates the remaining benefit value across the current cycle.

```text
Available Benefit
        -
Redeemed Benefit
        =
Unclaimed Benefit Value
```

### Step 4 — Apply Nudge Threshold

If the unclaimed value or engagement opportunity does not meet the configured threshold, the result is logged to the dashboard.

Otherwise, the member is passed to the ML scoring stage.

### Step 5 — Score Engagement Propensity

XGBoost estimates the likelihood of useful engagement using available spending/behavioral signals.

### Step 6 — Select Timing and Channel

The system selects the appropriate engagement moment based on spending patterns and configured rules.

### Step 7 — Send Nudge

The member receives a concise, benefit-specific message with a clear action.

Example:

> **$150 travel credit unused**  
> Book before it expires.

---

## Scalability Design

The architecture is designed around several scalability principles.

### Partitioned Warehouse

BigQuery is partitioned by benefit cycle and clustered by member to support large-scale analytical workloads.

### Config-Driven Rules

Entitlement logic is maintained in versioned YAML configuration rather than hard-coded application logic, allowing benefit rules to be updated without redeploying the core service.

### Batch-First ML

Portfolio-level propensity scoring can run nightly, while real-time processing is reserved for high-value triggers.

### Independent Services

Rules, valuation, and nudge engines can scale independently according to their compute requirements.

### Cached Dashboard Metrics

Redis can sit in front of FastAPI for read-heavy, once-per-cycle dashboard values.

### Multi-Tenant Isolation

Per-issuer BigQuery datasets support cost attribution and compliance isolation.

---

## Expected Impact

### Issuer

- Measure ROI of benefit investments
- Recover otherwise unclaimed benefit value
- Improve retention through proactive engagement
- Identify cross-sell and upsell signals
- Build a data-backed case for future benefit investments

### Card Members

- Discover benefits they have already paid for
- Improve awareness of available benefits
- Increase perceived card value
- Reduce unused benefit value

---

## Evaluation Metrics

The proposed solution defines the following success metrics:

| Metric | Target / Illustrative Value |
|---|---:|
| Entitlement mapping accuracy | 95%+ |
| Redemption uplift after nudges | +19 pts |
| Benefit value recovered | $2.1M |
| Reduction in unclaimed-value complaints | 30% |
| Nudge click-through rate | 25%+ |
| Card satisfaction / NPS lift | +8 pts |

> **Note:** These figures represent the project's proposed/illustrative success metrics rather than independently verified production results.

---

## Assumptions

The solution assumes:

- The issuer provides machine-readable benefit terms for each card SKU.
- MCC/merchant transaction data is available at T+1 or better.
- Redemption logs are accessible through issuer or partner APIs.
- Members opt in to notifications.
- Benefit dollar values are fixed or reasonably estimable.

---

## Constraints

Important real-world constraints include:

- Benefit rules vary across products and can change frequently.
- Some benefits are claims-based and cannot be proactively redeemed.
- PII and spending data require strict access controls.
- Nudge frequency must account for consent and notification fatigue.
- Real-time nudging involves a latency-versus-cost trade-off.

---

## Disclaimer

This repository is a project/prototype implementation based on the proposed Benefit-Underutilization Analytics solution. Any sample metrics, benefit values, or member data should be treated as illustrative unless explicitly identified as measured results from a real deployment.
