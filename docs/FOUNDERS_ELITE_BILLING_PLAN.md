# Nexora public launch: billing and Founders Edition (staging specification)

Status: DESIGN ONLY. No payment endpoint, checkout, production secret, or Cloudflare deployment is enabled by this document.

## Confirmed offer
- USD $250.00 one-time.
- Full Elite tier for the lifetime of the Nexora service, no recurring Elite membership fee.
- Exactly 50 confirmed purchasers maximum.
- Terms and refund policy must be approved before charging customers. Do not represent a limited quantity as available unless the backend can verify it.
- Standard Basic/Pro/Elite pricing remains undecided; do not invent prices.

## Architecture
1. Keep account identity and subscription entitlements in the Nexora backend, not the static Cloudflare website.
2. Use a payment provider such as Stripe Checkout. Server creates a one-time Checkout Session for a signed-in account. Price ID, product, amount (25000 cents), currency (usd), and mode (payment) must be configured and verified server-side; never trust browser-supplied price or entitlement.
3. Use a durable transactional database with unique constraints on customer/account and provider payment IDs. Maintain founder reservations with expiry and an atomic capacity check (confirmed + unexpired reservations <= 50). A checkout attempt must reserve a slot before session creation, and failed/expired sessions must release it.
4. Verify webhook signatures against raw request bytes. Treat webhook events as idempotent, tolerate retries and out-of-order delivery, and verify actual paid state and matching amount/currency/product/customer before assigning lifetime Elite.
5. Allocate sequential founder number 1..50 in a single database transaction only after confirmed payment; enforce unique founder number and unique lifetime entitlement per account. If an unexpected payment arrives after sellout, do not grant an extra slot; refund or escalate promptly.
6. Derive entitlements server-side: lifetime Elite takes precedence over recurring plans. Prevent duplicate billing; do not create recurring subscriptions for lifetime accounts. Reflect tier in desktop API without exposing payment credentials.
7. Define explicit refund/dispute rules and entitlement revocation. Keep an audit trail of purchases, webhook event IDs, reservations, entitlement changes and refund actions, with restricted access and no raw card details.
8. Display availability from a backend endpoint only after it is implemented. Never fake remaining slots, claim a sale succeeded based on a browser redirect, or collect card details on the static site.

## Minimum acceptance tests
- Concurrent checkout requests cannot reserve or grant >50.
- Duplicate and reordered webhooks never double-grant.
- Failed, cancelled, and expired checkouts do not grant Elite.
- A confirmed payment grants lifetime Elite exactly once.
- Incorrect amount/currency/product is rejected.
- Refund and dispute flows follow approved policy.
- Desktop and website show identical entitlements after login/logout.
- Provider test mode passes end-to-end; production credentials and webhook configuration reviewed before launch.

## Release boundary
Work only on feature/founders-elite-launch until approved. Do not merge, deploy to Cloudflare, charge cards, or enable live trading without explicit authorization.
