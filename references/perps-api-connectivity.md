# Kalshi Perps (Margin) API Connectivity

Official source: https://docs.kalshi.com/perps_openapi.yaml
Last ingested: 2026-08-28

"Perps", "margin", and "perpetual futures" are the same product. The API surface uses `margin` throughout (endpoints under `/margin`, margin-prefixed fields). It mirrors the event-contract API for auth, pagination, error format, and order lifecycle.

## REST API

| Environment | Base URL |
|-------------|----------|
| Demo | `https://external-api.demo.kalshi.co/trade-api/v2/margin/` |
| Production | `https://external-api.kalshi.com/trade-api/v2/margin/` |

Use the `external-api` hosts for perps REST. WebSocket and FIX use the separate hosts below.

## WebSocket API

| Environment | URL |
|-------------|-----|
| Demo | `wss://external-api-margin-ws.demo.kalshi.co/trade-api/ws/v2/margin` |
| Production | `wss://external-api-margin-ws.kalshi.com/trade-api/ws/v2/margin` |

## FIX API

Margin FIX uses a **separate host** from event-contract FIX. API keys should **not** be shared between the two FIX gateways.

### Endpoints

| Environment | Purpose | Host |
|-------------|---------|------|
| Demo | Order entry | `margin-fix.demo.kalshi.co` |
| Demo | Market data | `margin-marketdata.fix.demo.kalshi.co` |
| Production | Order entry | `margin-mm.fix.elections.kalshi.com` |
| Production | Market data | `margin-marketdata.fix.elections.kalshi.com` |

### Session types

| Purpose | Port | TargetCompID | Description |
|---------|------|--------------|-------------|
| Order Entry (no retransmission) | 8228 | `KalshiNR` | Submit, modify, cancel orders; no persistence/retransmission. Supports read-only listener sessions. |
| Order Entry (with retransmission) | 8230 | `KalshiRT` | Order entry with message retransmission. Supports read-only listener sessions. Contact `institutional@kalshi.com` for access. |
| Drop Copy | 8229 | `KalshiDC` | Request-response queries for historical execution reports. |
| Market Data | 8233 | `KalshiMD` | Order book snapshots and incremental updates. Market-data host only. |

### Session configuration

- Transport/protocol: **FIXT.1.1** with application version **FIX50SP2**.
- `SenderCompID`: your FIX API key (UUID format).
- `TargetCompID`: one of `KalshiNR`, `KalshiRT`, `KalshiDC`, `KalshiMD`.
- Session ID: `TargetCompID + SenderCompID`.
- Only one FIX connection per API key; separate API keys required for concurrent connections.

### SSL/TLS

- Must use **TLS 1.2+** (not plain TCP).
- Cipher suites follow AWS NLB TLS policies.
- If the FIX engine does not support native TLS, use a local proxy such as **stunnel**.
- To pin/persist the server certificate:
  ```bash
  openssl s_client -showcerts -connect <host>:<port> < /dev/null | openssl x509 > kalshi-fix.pem
  ```

### Private connectivity

- **AWS PrivateLink** available for network-level isolation (FIX traffic stays on AWS backbone).
- **Premier tier+**: contact `institutional@kalshi.com` to provision a PrivateLink endpoint.
- **Prime tier+**: contact `institutional@kalshi.com` to discuss VPC peering for production connectivity.

### Rate limits

- FIX application messages use the same token model, token costs, and margin Read/Write buckets as equivalent REST operations.
- Scope: application messages from client to server only.
- Excluded from rate limiting: Logout (`35=5`), Heartbeat (`35=0`), TestRequest (`35=1`).
- Logon (`35=A`) **is** rate-limited.
- Order-entry messages use the margin Write bucket.
- Mass Cancel Request (`35=q`) is limited to **1 request/second**.

### Maintenance window and pauses

- Scheduled maintenance times are listed under [Maintenance and Pauses](https://docs.kalshi.com/getting_started/maintenance_and_pauses).
- Sessions may be disconnected during maintenance. Kalshi does **not** reset sequence numbers; clients reset sequence numbers on their side when reconnecting.
- `KalshiRT` sessions retain message continuity across maintenance; missed messages can be retransmitted after reconnect.
- Tag `21006` (`CancelOrderOnPause`) on a New Order Single (`35=D`) controls resting-order behavior during a pause:
  - `Y` — order is canceled when a trading or exchange pause begins.
  - `N` (default) — order stays resting and resumes when activity reopens.

### Differences from event-contract FIX

|| | Event Contract FIX | Margin FIX |
||---|---|---|
|| Pricing | Integer cents (1–99) | Decimal dollars up to 4 decimal places |
|| Session types | 6 (NR, RT, DC, PT, RFQ, MD) | 4 (NR, RT, DC, MD) |
|| RFQ / Quotes | Supported | Not available |
|| Market settlement reports | Supported on `KalshiRT` | Not available |
|| `UseDollars` (21005) | Optional logon flag | Always enabled |

## FIX Order Entry

Source: Kalshi docs — FIX Margin Order Entry, extracted 2026-08-28.

### New Order Single (`35=D`)

| Tag | Name | Type | Required | Description |
|-----|------|------|----------|-------------|
| 11 | `ClOrderID` | String | Y | Client order identifier; UUID preferred |
| 18 | `ExecInst` | Char | N | `6 = Post Only` |
| 38 | `OrderQty` | Decimal | Y | Whole-number contract quantity |
| 40 | `OrdType` | Char | Y | `2 = Limit` |
| 44 | `Price` | Decimal | Y | Fixed-point dollars, up to 4 decimals |
| 54 | `Side` | Char | Y | `1 = Buy (bid)`, `2 = Sell (ask)` |
| 55 | `Symbol` | String | Y | Market ticker |
| 59 | `TimeInForce` | Char | N | `0 = Day`, `1 = GTC`, `3 = IOC`, `4 = FOK`, `6 = GTD` |
| 126 | `ExpireTime` | UTCTimestamp | C | Required when `TimeInForce = GTD` |
| 448 | `PartyID` | String | N | FCM customer-account or subaccount identifier |
| 452 | `PartyRole` | Integer | N | FCM only; `24 = Customer Account` |
| 453 | `NoPartyIDs` | Integer | N | FCM only; currently only `1` |
| 79 | `AllocAccount` | Integer | N | Subaccount number (0–63); alternative to NoPartyIDs |
| 526 | `SecondaryClOrdID` | UUID | N | Order group identifier |
| 2964 | `SelfTradePreventionType` | Integer | N | `1 = Taker At Cross`, `2 = Maker` |
| 21006 | `CancelOrderOnPause` | Boolean | N | Cancel the order if trading pauses |

Example:
```text
8=FIXT.1.1|9=200|35=D|34=5|52=20230809-12:34:56.789|49=your-api-key|56=KalshiNR|
11=550e8400-e29b-41d4-a716-446655440000|38=10.00|40=2|54=1|55=BTC-PERP|44=19.5000|
59=1|10=123|
```

### Order Cancel/Replace Request (`35=G`)

Supported modifications:
- `OrderQty`: increase or decrease quantity (increasing forfeits queue priority)
- `Price`: change limit price

| Tag | Name | Type | Required | Description |
|-----|------|------|----------|-------------|
| 11 | `ClOrderID` | String | Y | Unique modification request identifier |
| 37 | `OrderID` | String | N | Kalshi exchange order identifier |
| 38 | `OrderQty` | Decimal | Y | New total quantity for the order |
| 40 | `OrdType` | Char | Y | `2 = Limit` |
| 41 | `OrigClOrdID` | String | Y | `ClOrderID` of the order to modify |
| 44 | `Price` | Decimal | N | New fixed-point dollar price |
| 54 | `Side` | Char | Y | Must match original side |
| 55 | `Symbol` | String | Y | Must match original ticker |
| 448 | `PartyID` | String | N | FCM customer-account/subaccount |
| 452 | `PartyRole` | Integer | N | FCM party role |
| 453 | `NoPartyIDs` | Integer | N | FCM party count |
| 79 | `AllocAccount` | Integer | N | Subaccount number |

### Order Cancel Request (`35=F`)

Cancel all remaining quantity of an existing order.

| Tag | Name | Type | Required | Description |
|-----|------|------|----------|-------------|
| 11 | `ClOrderID` | String | Y | Unique cancel request identifier |
| 37 | `OrderID` | String | N | Kalshi exchange order identifier |
| 41 | `OrigClOrdID` | String | Y | `ClOrderID` of the order to cancel |
| 54 | `Side` | Char | Y | Must match original side |
| 55 | `Symbol` | String | Y | Must match original ticker |
| 448 | `PartyID` | String | N | FCM customer-account/subaccount |
| 452 | `PartyRole` | Integer | N | FCM party role |
| 453 | `NoPartyIDs` | Integer | N | FCM party count |
| 79 | `AllocAccount` | Integer | N | Subaccount number |

### Execution Report (`35=8`)

Exchange-to-client order-state update.

| Tag | Name | Type | Required | Description |
|-----|------|------|----------|-------------|
| 6 | `AvgPx` | Decimal | Y | Average fill price |
| 11 | `ClOrderID` | String | Y | `ClOrderID` from the last change-making request |
| 14 | `CumQty` | Decimal | Y | Total filled quantity |
| 17 | `ExecID` | String | Y | Unique sequenced report identifier |
| 30 | `LastMkt` | String | C | Exchange index that produced the report |
| 31 | `LastPx` | Decimal | C | Price of last fill |
| 32 | `LastQty` | Decimal | C | Quantity of last fill |
| 37 | `OrderID` | String | Y | Exchange order identifier |
| 38 | `OrderQty` | Decimal | Y | Defaults to `LeavesQty + CumQty`; if `21008=Y`, original order quantity |
| 39 | `OrdStatus` | Char | Y | Current order status |
| 41 | `OrigClOrdID` | String | C | Previous `ClOrderID` for replaced/canceled orders |
| 44 | `Price` | Decimal | C | Limit price |
| 54 | `Side` | Char | Y | Original side |
| 55 | `Symbol` | String | Y | Margin market ticker |
| 58 | `Text` | String | N | Human-readable result description |
| 60 | `TransactTime` | UTCTimestamp | Y | Timestamp for the triggering event |
| 103 | `OrdRejReason` | Integer | C | Rejection reason when `ExecType = Rejected` |
| 126 | `ExpireTime` | UTCTimestamp | C | Expiration timestamp |
| 150 | `ExecType` | Char | Y | Why this report was sent |
| 151 | `LeavesQty` | Decimal | Y | Remaining open quantity |
| 448 | `PartyID` | String | N | FCM customer-account/subaccount |
| 452 | `PartyRole` | Integer | N | FCM party role |
| 453 | `NoPartyIDs` | Integer | N | FCM party count |
| 79 | `AllocAccount` | Integer | C | Subaccount number |

#### Order Status (`39`)

- `New<0>`
- `Partially Filled<1>`
- `Filled<2>`
- `Canceled<4>`
- `Replaced<5>`
- `Pending Cancel<6>`
- `Rejected<8>`
- `Pending New<A>`
- `Expired<C>`
- `Pending Replace<E>`

Note: with default settings, expiry-style system cancellations report as `Canceled<4>`. If `21012 (UseExpiredOrdStatus)=Y`, they emit `Expired<C>`.

#### Order Rejection Reasons (`103`)

- `Unknown symbol<1>`
- `Exchange closed<2>`
- `Order exceeds limit<3>`
- `Too late to enter<4>`
- `Stale order<5>`
- `Duplicate order<6>`
- `Unsupported order characteristic<11>`
- `Incorrect quantity<13>`
- `Unknown account<15>`
- `Other<99>`

#### Execution Types (`150`)

- `New<0>`
- `Trade<F>`
- `Canceled<4>`
- `Replaced<5>`
- `Rejected<8>`
- `Expired<C>`
- `Pending New<A>`
- `Pending Cancel<6>`
- `Pending Replace<E>`

#### Text field values (`58`)

Common values: `EXCHANGE_UNAVAILABLE`, `INTERNAL_ERROR`, `MARKET_ALREADY_CLOSED`, `MARKET_INACTIVE`, `MARKET_NOT_FOUND`, `SELF_CROSS_ATTEMPT`, `ORDER_ALREADY_EXISTS`, `EXCEEDED_PER_MARKET_RISK_LIMIT`, `EXCEEDED_ORDER_GROUP_RISK_LIMIT`, `ORDER_GROUP_NOT_FOUND`, `FOK_INSUFFICIENT_VOLUME`, `POST_ONLY_CROSS`, `ORDER_GROUP_CANCEL`, `TAKER_CANCEL_FOR_SELF_TRADE_PREVENTION`, `MAKER_CANCEL_FOR_SELF_TRADE_PREVENTION`, `IMMEDIATE_OR_CANCELLED`.

#### OrderCancelReject (`35=9`)

Amend/cancel failures return `OrderCancelReject`, not `ExecutionReport`.

| Text (`58`) | `CxlRejReason` (`102`) |
|-------------|------------------------|
| `INVALID_AMEND_QTY_FOR_ORDER` | Broker |
| `CANNOT_UPDATE_FILLED_ORDER` | Broker |
| `SELF_CROSS_ATTEMPT` | Invalid price increment |

#### Position and fee information (on `ExecType = Trade`)

| Tag | Name | Description |
|-----|------|-------------|
| 704 | `LongQty` | Net long position after trade |
| 705 | `ShortQty` | Net short position after trade |
| 136 | `NoMiscFees` | Number of fees |
| 137 | `MiscFeeAmt` | Total fees in dollars |
| 138 | `MiscFeeCurr` | Currency (`USD`) |
| 139 | `MiscFeeType` | Exchange fees |
| 891 | `MiscFeeBasis` | Always `ABSOLUTE<0>` |
| 880 | `TrdMatchID` | Trade identifier |
| 1057 | `AggressorIndicator` | Taker/maker flag |

#### Collateral changes

| Tag | Name | Description |
|-----|------|-------------|
| 1703 | `NoCollateralAmountChanges` | Number of collateral changes |
| 1704 | `CollateralAmountChange` | Delta in dollars |
| 1705 | `CollateralAmountType` | Balance or payout |

### Mass Cancel Request (`35=q`)

Cancel all orders for the trading session. Only available on `KalshiNR`.

| Tag | Name | Description |
|-----|------|-------------|
| 11 | `ClOrderID` | Unique request ID |
| 530 | `MassCancelRequestType` | `Cancel for session<6>` |

### Mass Cancel Report (`35=r`)

Response to mass cancel request.

| Tag | Name | Description |
|-----|------|-------------|
| 11 | `ClOrderID` | Request ID |
| 37 | `OrderID` | Operation ID |
| 531 | `MassCancelResponse` | `Success<6>` or `Rejected<0>` |
| 532 | `MassCancelRejectReason` | If rejected |

Individual `ExecutionReport` messages follow for each cancelled order.

## FIX Order Groups

Source: Kalshi docs — FIX Margin Order Groups (`/fix-margin/order-groups`), extracted 2026-08-28.

Manage margin order groups via `Order Group Request (35=UOG)`; responses come back
as `Order Group Response (35=UOH)`. Create, Reset, Delete, Trigger, and Update are
the five actions (tag `20131`).

The underlying trigger mechanism — a contracts limit enforced over a **rolling
15-second window** — is defined in the Kalshi **Order Groups overview**
(`/getting_started/order_groups`), not this FIX page. See
[Group trigger mechanism (from Order Groups overview)](#group-trigger-mechanism-from-order-groups-overview)
below for the Active/Triggered state machine and when a group auto-triggers. On
this page, the rolling window appears only as the Action=5 (Update) edge case.

### Order Group Request (`35=UOG`)

| Tag | Name | Type | Required | Description |
|-----|------|------|----------|-------------|
| 20131 | `OrderGroupAction` | Int | Y | `1 = Create`, `2 = Reset`, `3 = Delete`, `4 = Trigger`, `5 = Update` |
| 20130 | `OrderGroupID` | UUID | C | Group ID. Server‑generated on Create; required for Reset/Delete/Trigger/Update. Do not send on Create. |
| 20132 | `OrderGroupContractsLimit` | Int | C | Max contracts allowed, `1`–`1,000,000`. Required on Create; new limit on Update. |

Required fields by action:

- **Create (1):** `20132` (limit) required. Server returns the new `OrderGroupID` in `35=UOH`. Do **not** include `20130`.
- **Reset (2):** `20130` required. Clears the triggered state so the group can be reused.
- **Delete (3):** `20130` required. Cancels all resting orders in the group.
- **Trigger (4):** `20130` required. Immediately cancels all orders in the group regardless of whether the contracts limit has been reached.
- **Update (5):** `20130` + `20132` (new limit) required. If the updated limit would immediately trigger the group based on the rolling 15-second window, the server cancels all orders in the group and marks it triggered until reset.

Wire examples (verbatim from Kalshi docs):

```text
# Create Margin Order Group
8=FIXT.1.1|9=150|35=UOG|34=5|52=20230809-12:34:56.789|49=your-api-key|56=KalshiNR|
20131=1|20132=5000|10=123|

# Reset Margin Order Group
8=FIXT.1.1|9=150|35=UOG|34=6|52=20230809-12:34:57.789|49=your-api-key|56=KalshiNR|
20131=2|20130=770e8400-e29b-41d4-a716-446655440002|10=124|

# Delete Margin Order Group
8=FIXT.1.1|9=150|35=UOG|34=7|52=20230809-12:34:58.789|49=your-api-key|56=KalshiNR|
20131=3|20130=770e8400-e29b-41d4-a716-446655440002|10=125|

# Trigger Margin Order Group
8=FIXT.1.1|9=150|35=UOG|34=8|52=20230809-12:34:59.789|49=your-api-key|56=KalshiNR|
20131=4|20130=770e8400-e29b-41d4-a716-446655440002|10=126|

# Update Margin Order Group Limit
8=FIXT.1.1|9=150|35=UOG|34=9|52=20230809-12:35:00.789|49=your-api-key|56=KalshiNR|
20131=5|20130=770e8400-e29b-41d4-a716-446655440002|20132=2500|10=127|
```

Implementation note: the `9=` (BodyLength) and `10=` (CheckSum) values above are
Kalshi's published examples. A real FIX engine must compute `9` and `10` per
outbound message rather than copying these literals.

### Order Group Response (`35=UOH`)

Response to order group management requests.

| Tag | Name | Description |
|-----|------|-------------|
| 20130 | `OrderGroupID` | ID of the order group (server‑generated on Create). |

### Errors

- **Business-logic errors** (group not found, exchange-returned errors) → `BusinessMessageReject (35=j)`.
- **Malformed fields** (e.g. invalid UUID format for `OrderGroupID`) → session-level `Reject (35=3)`.

See also `FIX Error Handling` below for the full reject taxonomy.

### Group trigger mechanism (from Order Groups overview)

Source: Kalshi docs — Order Groups overview (`/getting_started/order_groups`), extracted 2026-08-28.

Order groups provide automatic order cancellation when a contracts limit is reached
within a rolling 15-second window. When a group is triggered, all resting orders in
that group are canceled and no new orders can be placed until the group is reset.

**Group states:**

| State | Behavior |
|-------|----------|
| **Active** | Orders can be placed; rolling volume is tracked against the limit |
| **Triggered** | All resting orders canceled; new orders rejected until the group is reset |

A group enters the **triggered** state when:

- the rolling 15-second volume exceeds the contracts limit,
- a manual **Trigger** action is issued (cancels all orders regardless of whether the limit is reached), or
- the limit is **Updated** to a value below the current rolling volume.

**Reset** clears the triggered state and the rolling-volume counter, returning the
group to active. **Delete** removes the group entirely and cancels all resting
orders in it.

The Order Groups overview is protocol-neutral / shared documentation; use the
protocol-specific REST and FIX pages for surface-specific message and endpoint
details.

### Wire notes / bot integration

- **REST path:** attach an existing group to a new order via the JSON field `order_group_id` on `POST /margin/orders`. A client should set it when the intent carries an `order_group_id`. The docs describe tagging orders into a pre-existing group; group lifecycle (create/manage) is a separate `35=UOG` conversation (see FIX Order Entry).
- **FIX path:** attach a group to a `New Order Single (35=D)` via tag `526` (`SecondaryClOrdID`) = the `OrderGroupID` (see FIX Order Entry). Group lifecycle (Create/Reset/Delete/Trigger/Update) is a separate `35=UOG` conversation.
- **Streaming:** group state changes arrive on the margin WS channel `order_group_updates` (already subscribed in `PerpsChannel.ORDER_GROUP_UPDATES`).

## FIX Authentication & Sessions

Source: Kalshi docs — FIX Margin Authentication & Sessions, extracted 2026-08-28.

### API key setup

- FIX API keys use the same RSA key pair as the REST API.
- Generate a 2048-bit RSA key pair and register the public key in your Kalshi account profile.
- The resulting API Key ID (UUID) is your `SenderCompID`.
- Key generation commands:
  ```bash
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out kalshi-fix.key
  openssl rsa -in kalshi-fix.key -pubout -out kalshi-fix.pub
  ```

### Logon (`35=A`)

- Initiator sends Logon; acceptor replies with Logon (success) or Logout (failure).

#### Required fields

| Tag | Name | Value |
|-----|------|-------|
| 98 | `EncryptMethod` | `None<0>` |
| 96 | `RawData` | Base64-encoded PSS RSA signature |
| 1137 | `DefaultApplVerID` | `FIX50SP2<9>` |

#### Optional fields

| Tag | Name | Description | Default |
|-----|------|-------------|---------|
| 141 | `ResetSeqNumFlag` | Reset sequence numbers on logon. **Must be `Y` for KalshiNR and KalshiDC.** | `N` |
| 108 | `HeartbeatInt` | Heartbeat interval in seconds; must be `>= 3`. | `30` |
| 8013 | `CancelOrdersOnDisconnect` | Cancel all open orders on disconnect **(consequence triggers at Logout if set to Y here)**. | `N` |
| 20126 | `ListenerSession` | Listen-only session. **KalshiNR/KalshiRT only; requires `SkipPendingExecReports=Y`.** | `N` |
| 20200 | `MessageRetentionPeriod` | Hours session messages stored for retransmission (max 72). **KalshiRT only.** | `24` |
| 21005 | `UseDollars` | Fixed-point dollar pricing flag. Always enabled for margin. | Always on |
| 21011 | `SkipPendingExecReports` | Skip `PENDING_NEW` / `PENDING_REPLACE` / `PENDING_CANCEL` exec reports. | `N` |
| 21012 | `UseExpiredOrdStatus` | Emit `Expired<C>` instead of `Canceled<4>` for expiry-style system cancellations. | `N` |
| 21007 | `EnableIocCancelReport` | Partially filled IOC orders produce a cancel report. | `N` |
| 21008 | `PreserveOriginalOrderQty` | `OrderQty` (38) always reflects original order quantity across states. | `N` |

> Note: Tag `21006` (`CancelOrderOnPause`) is **not** a Logon option; it is set per order on `New Order Single (35=D)`.

### Signature generation

`RawData` must contain a **PSS RSA signature** (SHA-256 hash) of the pre-hash string:

```text
PreHashString = SendingTime + SOH + MsgType + SOH + MsgSeqNum + SOH + SenderCompID + SOH + TargetCompID
```

- The `SendingTime` in the pre-hash string must match field 52 (`SendingTime`) in the Logon message exactly.
- `SendingTime` must be within **30 seconds** of server time, or the Logon is rejected with `SessionRejectReason<373>=10`.
- Python example:
  ```python
  from base64 import b64encode
  from Cryptodome.Signature import pss
  from Cryptodome.Hash import SHA256
  from Cryptodome.PublicKey import RSA

  private_key = RSA.import_key(open('kalshi-fix.key').read().encode('utf-8'))

  sending_time = "20230809-05:28:18.035"
  msg_type = "A"
  msg_seq_num = "1"
  sender_comp_id = "your-fix-api-key-uuid"
  target_comp_id = "KalshiNR"

  msg_string = chr(1).join([
      sending_time, msg_type, msg_seq_num,
      sender_comp_id, target_comp_id
  ])

  msg_hash = SHA256.new(msg_string.encode('utf-8'))
  signature = pss.new(private_key).sign(msg_hash)
  raw_data_value = b64encode(signature).decode('utf-8')
  ```

### Heartbeat & sequence numbers

| Behavior | Detail |
|----------|--------|
| Default heartbeat interval | 30 seconds |
| Missed heartbeat | Connection terminates if heartbeat response not received within interval |
| Sequence number lower than expected | Connection terminated |
| Sequence number higher than expected | Recoverable with `ResendRequest` (KalshiRT only) |

### Message retransmission

- `ResendRequest` / `SequenceReset` are supported **only on KalshiRT**.
- `ResetSeqNumFlag<141>` must always be `Y` on KalshiNR and KalshiDC.
- KalshiRT retention window is controlled by `MessageRetentionPeriod` (default 24h, max 72h).
- `ResendRequest<35=2>` fields:

| Tag | Name | Description |
|-----|------|-------------|
| 7 | `BeginSeqNo` | Lower bound (inclusive) |
| 16 | `EndSeqNo` | Upper bound (inclusive) |

### Logout (`35=5`)

- Either side may initiate Logout; the counterparty responds with Logout and the transport connection is terminated.
- If `CancelOrdersOnDisconnect=Y` was set on Logon, all open orders are canceled on disconnect.

## REST API reference notes

- Authentication, pagination, error format, and core order lifecycle (create, amend, decrease, cancel) work identically to event contracts, under `/margin/*`.
- Margin-specific additions: account balance/risk, funding (estimated/historical rates, payment history), fee tiers, subaccounts, and event-contract ↔ margin transfers.
- `/margin/enabled` checks whether margin is enabled for the account in the current environment.
- `/portfolio/intra_exchange_instance_transfer` is **not yet available**.

**Not available on margin REST:**
- Batch order operations (`BatchCreateOrders`, `BatchCancelOrders`)
- Queue positions
- Events, series, milestones, multivariate collections, structured targets
- RFQs and quotes
- Historical data endpoints
- Exchange schedule

## Margin REST Endpoints

Individual margin/perps REST endpoints. All paths on this surface require the
standard Kalshi REST auth headers and — per the margin signing rule — the
request must be signed over the **full `/margin` path** (`/trade-api/v2/margin/...`)
or every private margin endpoint returns `401`.

### POST /margin/fcm/subtraders — Create Margin FCM Subtrader

Source: Kalshi docs — Create Margin FCM Subtrader
(`/margin-rest/fcm/create-margin-fcm-subtrader`), extracted 2026-08-28.

FCM members create a **margin subtrader** (sub-account). The full subtrader id
is composed server-side as `{user_id}_{subtrader_suffix}`.

**URLs**

| Environment | URL |
|-------------|-----|
| Demo | `https://external-api.demo.kalshi.co/trade-api/v2/margin/fcm/subtraders` |
| Production | `https://external-api.kalshi.com/trade-api/v2/margin/fcm/subtraders` |

**Auth — required request headers**

| Header | Type | Description |
|--------|------|-------------|
| `KALSHI-ACCESS-KEY` | string | Your API key ID |
| `KALSHI-ACCESS-SIGNATURE` | string | RSA-PSS signature of the request |
| `KALSHI-ACCESS-TIMESTAMP` | string | Request timestamp in milliseconds |

**Request body** (`application/json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subtrader_suffix` | string | Y | Suffix for the new subtrader. Pattern `^[a-z0-9]{1,16}$`. Server composes the full id as `{user_id}_{subtrader_suffix}`. |

**Response `201 Created`** (`application/json`) — "Subtrader created successfully"

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subtrader_id` | string | Y | Full id of the created subtrader, in the form `{user_id}_{subtrader_suffix}`. |

**Error responses** — `400`, `401`, `403`, `409`, `500` all return the same envelope:

```json
{ "code": "<string>", "message": "<string>", "details": "<string>" }
```

**Signing note (margin REST):** the signature must cover the full path including
`/margin` — `/trade-api/v2/margin/fcm/subtraders`. A request signed as
`/trade-api/v2/fcm/subtraders` (dropping `/margin`) is rejected with `401` on
every authenticated margin endpoint. The bot's margin REST client already signs
`f"/trade-api/v2/margin{path}"` via `_sign_request`.

**Docs navigation:** previous → Price Banding (`/margin/price-banding`); next →
Get FCM Subtrader Risk Controls (`/margin-rest/fcm/get-fcm-subtrader-risk-controls`).

### POST /margin/orders — Create Order

Source: Kalshi docs — Create Order (`/margin-rest/orders/create-order`), extracted
2026-08-28.

Place a margin/perps order. This is the REST order-entry endpoint the bot's
`PerpsOrderBuilder.build_create` targets (see Wire notes below).

**URLs**

| Environment | URL |
|-------------|-----|
| Demo | `https://external-api.demo.kalshi.co/trade-api/v2/margin/orders` |
| Production | `https://external-api.kalshi.com/trade-api/v2/margin/orders` |

**Auth — required request headers**

| Header | Type | Description |
|--------|------|-------------|
| `KALSHI-ACCESS-KEY` | string | Your API key ID |
| `KALSHI-ACCESS-SIGNATURE` | string | RSA-PSS signature of the request |
| `KALSHI-ACCESS-TIMESTAMP` | string | Request timestamp in milliseconds |
| `Content-Type` | string | `application/json` |

**Request body** (`application/json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Y | Market ticker |
| `client_order_id` | string | Y | Client order identifier (must be unique per order) |
| `side` | enum<string> | Y | `bid` or `ask` |
| `count` | string | Y | Order quantity in contracts, as a string. Example `"10.00"` |
| `price` | string | Y | Fixed-point dollars. Example `"0.5600"` |
| `time_in_force` | enum<string> | Y | `fill_or_kill`, `good_till_canceled`, `immediate_or_cancel` |
| `self_trade_prevention_type` | enum<string> | Y | `taker_at_cross` or `maker`. `taker_at_cross` cancels the taker order when it would cross against another order from the same user (execution stops; partial fills already matched are executed). `maker` cancels the resting maker order and continues matching |
| `expiration_time` | integer<int64> | N | Expiration time (Unix ms) |
| `post_only` | boolean | N | Resting-only; order rejects if it would cross |
| `cancel_order_on_pause` | boolean | N | If `true`, the order is canceled when it is open and trading on the exchange is paused for any reason |
| `reduce_only` | boolean | N | Caps the place count by the member's current position. **Rejected unless `time_in_force` is `immediate_or_cancel` or `fill_or_kill`** (the margin API rejects `reduce_only` with `good_till_canceled`) |
| `subaccount` | integer | N (default `0`, `x >= 0`) | Subaccount number; `0` is the primary subaccount |
| `order_group_id` | string | N | The order group this order is part of |

> Doc inconsistency note: the page's example JSON payload omits `side`, but the
> parameter reference lists `side` as **required**. Treat `side` as required — the
> bot's `build_create` always sets it. The example payload also lists `post_only`,
> `cancel_order_on_pause`, `reduce_only`, `subaccount`, `order_group_id`,
> `expiration_time` (all optional per the param table).

**Response `201 Created`** (`application/json`) — "Order created successfully"

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | Y | Exchange-assigned order id |
| `fill_count` | string | Y | Contracts filled immediately upon placement. Example `"10.00"` |
| `remaining_count` | string | Y | Contracts remaining after placement. For IOC orders, reflects the final state after unfilled contracts are canceled. Example `"10.00"` |
| `client_order_id` | string | N | Echo of the client order id |
| `average_fill_price` | string | N | Volume-weighted average fill price. **Only present when `fill_count > 0`** |
| `average_fee_paid` | string | N | Volume-weighted average fee per contract for fills from this request. **Only present when `fill_count > 0`** |

**Error responses** — `400`, `401`, `409`, `429`, `500` all return the same envelope:

```json
{ "code": "<string>", "message": "<string>", "details": "<string>" }
```

**Signing note (margin REST):** the signature must cover the full path including
`/margin` — `/trade-api/v2/margin/orders`. A request signed as
`/trade-api/v2/orders` (dropping `/margin`) is rejected with `401` on every
authenticated margin endpoint. The bot's margin REST client signs
`f"/trade-api/v2/margin{path}"` via `_sign_request`.

**Wire notes / bot integration:**
- `PerpsOrderBuilder.build_create` sets `ticker`, `client_order_id`, `side`,
  `count`, `price`, `time_in_force`, `self_trade_prevention_type`, and
  `order_group_id` (when `intent.order_group_id` is present). It raises
  `PerpsOrderValidationError(REDUCE_ONLY_TIF)` when `reduce_only` is set with a TIF
  outside `{immediate_or_cancel, fill_or_kill}` — encoding the API constraint
  before the request reaches the gateway.
- `count` and `price` are **strings** on this surface (fixed-point dollars / contract
  counts), not numbers. The bot builds them as strings.

### GET /margin/orders — Get Orders

Source: Kalshi docs — Get Orders (`/margin-rest/orders/get-orders`), extracted
2026-08-28.

List margin/perps orders with cursor pagination.

**URLs**

| Environment | URL |
|-------------|-----|
| Demo | `https://external-api.demo.kalshi.co/trade-api/v2/margin/orders` |
| Production | `https://external-api.kalshi.com/trade-api/v2/margin/orders` |

**Auth — required request headers:** same as Create Order (`KALSHI-ACCESS-KEY`,
`KALSHI-ACCESS-SIGNATURE`, `KALSHI-ACCESS-TIMESTAMP`).

**Query parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | N | Filter by market ticker |
| `min_ts` | integer<int64> | N | Filter items after this Unix timestamp |
| `max_ts` | integer<int64> | N | Filter items before this Unix timestamp |
| `status` | string | N | Filter by status |
| `limit` | integer<int64> | N (default `10000`, `1 <= x <= 10000`) | Orders per page |
| `cursor` | string | N | Pagination cursor; empty for first page |
| `subaccount` | integer | N (`x >= 0`) | Subaccount number (`0` primary, `1`–`63`); omitted = all subaccounts |

**Response `200 OK`** (`application/json`) — "Orders retrieved successfully"

```json
{
  "orders": [
    {
      "order_id": "<string>",
      "user_id": "<string>",
      "client_order_id": "<string>",
      "ticker": "<string>",
      "side": "bid",
      "last_update_reason": "",
      "price": "0.5600",
      "fill_count": "10.00",
      "remaining_count": "10.00",
      "expiration_time": "2023-11-07T05:31:56Z",
      "created_time": "2023-11-07T05:31:56Z",
      "last_update_time": "2023-11-07T05:31:56Z",
      "self_trade_prevention_type": "taker_at_cross",
      "cancel_order_on_pause": true,
      "order_group_id": "<string>",
      "order_source": "user",
      "order_reason": "liquidation"
    }
  ],
  "cursor": "<string>"
}
```

Note: REST order objects use **RFC3339** timestamps (`expiration_time`,
`created_time`, `last_update_time`), unlike the margin WebSocket `user_orders`
channel which uses `*_ts_ms` Unix-ms fields. Normalize per surface before comparing.

**Error responses** — `400`, `401`, `500` return the same envelope as Create Order:

```json
{ "code": "<string>", "message": "<string>", "details": "<string>" }
```

**Docs navigation:** previous → Get Orders (`/margin-rest/orders/get-orders`); next →
Cancel All Orders (`/margin-rest/orders/cancel-all-orders`).

### DELETE /margin/orders — Cancel All Orders

Source: Kalshi docs — Cancel All Orders
(`/margin-rest/orders/cancel-all-orders`), extracted 2026-08-28.

Cancels **all resting margin orders** for the authenticated Direct member. This is
the margin/perps surface's "flatten resting book" control — a single `DELETE`
replaces N individual `DELETE /margin/orders/{order_id}` calls. Treat it as a
potentially destructive, account-wide action.

- If `subaccount` is **omitted**, matching orders may come from **any** subaccount.
- If `subaccount` is **provided**, only orders for that subaccount are eligible.
- **Trailing-cancel window:** newly placed orders may **also** be cancelled during
  the **minute after** the request — do not place fresh orders in the 60s after a
  cancel-all, or they may be swept too.

**URLs**

| Environment | URL |
|-------------|-----|
| Demo | `https://external-api.demo.kalshi.co/trade-api/v2/margin/orders` |
| Production | `https://external-api.kalshi.com/trade-api/v2/margin/orders` |

**Auth — required request headers:** same as Create Order (`KALSHI-ACCESS-KEY`,
`KALSHI-ACCESS-SIGNATURE`, `KALSHI-ACCESS-TIMESTAMP`). No request body.

**Query parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount` | integer | N (`x >= 0`) | Subaccount number (`0` primary, `1`–`63`); omitted = all subaccounts. If provided, only that subaccount's resting orders are eligible |

**Response `204 No Content`** — no body. "All matching resting margin orders were
cancelled."

**Error responses** — `401`, `429`, `500` return the same envelope as Create Order:

```json
{ "code": "<string>", "message": "<string>", "details": "<string>" }
```

> **Rate limit:** a cancel-all request consumes the **same number of write tokens**
> as a batch cancel containing the **maximum number of orders** allowed for the
> caller's margin API tier. One `DELETE` can burn a tier's whole batch budget even
> if only a few orders were resting — budget it like a max-size batch cancel, not a
> single order cancel.

**Signing note (margin REST):** the signature must cover the full path including
`/margin` — `/trade-api/v2/margin/orders`. A request signed as `/trade-api/v2/orders`
(dropping `/margin`) is rejected with `401` on every authenticated margin endpoint.
The bot's margin REST client signs `f"/trade-api/v2/margin{path}"` via `_sign_request`.
For `DELETE` with no body, the pre-hash string is `timestamp` + `DELETE` + `path`
(empty body — do not append a body hash).

**Wire notes / bot integration:**
- Clients have **no dedicated cancel-all helper in this skill**. Prefer a single guarded
  call to `DELETE /margin/orders` over looping per-order cancels
  when the intent is genuinely "flatten everything resting." Gate it behind an
  explicit operator confirmation and log the response — it is account-wide and
  irreversible.
- **Always pass `subaccount` explicitly** when the bot manages a specific subaccount.
  An unqualified cancel-all will sweep resting orders on *every* subaccount the key
  can see, including ones the strategy intends to keep working.
- Respect the **1-minute trailing-cancel window**: after issuing cancel-all, hold new
  order placement for ≥60s (or accept that freshly placed orders may be cancelled).
  A reconcile that places a "replacement" order inside that window will cancel itself.
- Rate-limit accounting: charge the cancel-all against the write-token budget as a
  full max-size batch cancel (see Rate limit note), so a single call does not silently
  exhaust the budget mid-cycle.
- Response is `204` with **no JSON body** — do not parse an order list back. Treat
  `204` as success; treat any `401`/`429`/`500` envelope as failure and fail closed.

**Docs navigation:** previous → Cancel All Orders (`/margin-rest/orders/cancel-all-orders`); next →
Get Order (`/margin-rest/orders/get-order`).

## WebSocket API reference notes

**Same channels as event contracts:** `orderbook_delta`, `ticker`, `trade`, `fill`, `user_orders`, `order_group_updates`.

**Not available on margin WS:** `market_positions`, `market_lifecycle_v2`, `multivariate_market_lifecycle`, `multivariate`, `communications`.

**Timestamp convention:** all margin WebSocket timestamps are Unix epoch milliseconds with an `_ms` suffix.

| Channel | Event contract | Margin |
|---------|---------------|--------|
| `orderbook_delta` | `ts` as RFC3339 | `ts_ms` as Unix ms |
| `ticker` | `ts` Unix seconds, `time` RFC3339 | `ts_ms` top level; nested `reference_price` / `settlement_mark_price` / `liquidation_mark_price` each have `ts_ms`; `funding_rate` has `next_funding_time_ms` and `ts_ms` |
| `trade` | `ts` Unix seconds | `ts_ms` Unix ms |
| `fill` | `ts` Unix seconds | `ts_ms` Unix ms |
| `user_orders` | `created_time`, `last_update_time`, `expiration_time` as RFC3339 | `created_ts_ms`, `last_updated_ts_ms`, `expiration_ts_ms` as Unix ms |

## Relation to BTC15M

KXBTC15M is an **event-contract** market. It uses the event-contract endpoints (`/portfolio/*`, `/markets/*`, event-contract FIX/WebSocket hosts) and integer-cent pricing — **not** the perps/margin namespace. Keep these gateways separate in any multi-product code.

## Price Banding

Source: Kalshi docs — Price Banding, extracted 2026-08-28.

For perpetual (margin) markets:

- Tick size: **0.0001 USD** per price point.
- **Bid floor:** a new/resting bid must be **≥** the **lower** of:
  - 80% of the current best bid, **or**
  - best bid − 1,000 ticks (`best_bid − 0.1000`).
- **Ask ceiling:** a new/resting ask must be **≤** the **higher** of:
  - 120% of the current best ask, **or**
  - best ask + 1,000 ticks (`best_ask + 0.1000`).

### Operational notes

- Resting orders are **not canceled** when the band moves.
- If there are **no resting orders on a side**, there is **no band limit for that side**.
- Order **amends outside the band are not allowed**.

This applies only to margin/perps markets. Event-contract markets (e.g. KXBTC15M) have their own price-grid rules and should not use this band logic.

## FIX Error Handling

Source: https://docs.kalshi.com/fix-margin/error-handling (extracted 2026-08-28).

Errors fall into two categories:
- **Session-level errors**: protocol violations → `Reject (35=3)`
- **Business-level errors**: application logic issues → `BusinessMessageReject (35=j)` or order-specific rejection messages

### Reject (`35=3`) — session-level

| Tag | Name | Description | Required |
|-----|------|-------------|----------|
| 45 | `RefSeqNum` | Sequence number of rejected message | Y |
| 58 | `Text` | Human-readable error description | N |
| 371 | `RefTagID` | Tag that caused the rejection | N |
| 372 | `RefMsgType` | Message type being rejected | N |
| 373 | `SessionRejectReason` | Rejection reason code | N |

#### Session Reject Reasons (`373`)

| Code | Reason | Description |
|------|--------|-------------|
| 0 | Invalid tag number | Unknown tag in message |
| 1 | Required tag missing | Mandatory field not present |
| 2 | Tag not defined for message | Tag not valid for this message type |
| 3 | Undefined tag | Tag number not in FIX specification |
| 4 | Tag without value | Empty tag value |
| 5 | Incorrect value | Invalid value for tag |
| 6 | Incorrect data format | Wrong data type |
| 8 | Signature problem | Authentication failure |
| 9 | CompID problem | `SenderCompID` / `TargetCompID` issue |
| 10 | SendingTime accuracy | `SendingTime` must be within 30 seconds of server time |
| 11 | Invalid MsgType | Unknown message type |

### BusinessMessageReject (`35=j`) — business-level

| Tag | Name | Description | Required |
|-----|------|-------------|----------|
| 45 | `RefSeqNum` | Sequence number of rejected message | Y |
| 58 | `Text` | Human-readable error description | N |
| 372 | `RefMsgType` | Message type being rejected | Y |
| 379 | `BusinessRejectRefID` | Business ID from rejected message | N |
| 380 | `BusinessRejectReason` | Business rejection reason code | Y |

#### Business Reject Reasons (`380`)

| Code | Reason | Description |
|------|--------|-------------|
| 0 | Other | See `Text` field |
| 1 | Unknown ID | Referenced ID not found |
| 2 | Unknown Security | Invalid symbol |
| 3 | Unsupported Message Type | Message type not implemented on this margin session |
| 4 | Application not available | System temporarily unavailable |
| 5 | Conditionally required field missing | Context-specific field missing |

### Order-specific rejections

New-order rejections come in `ExecutionReport (35=8)` with `ExecType=Rejected` and `OrdRejReason (103)`. Amend/cancel failures come in `OrderCancelReject (35=9)` with `CxlRejReason (102)`.

#### Order Reject Reasons (`103`)

In `ExecutionReport` with `150=8`:

| Code | Reason | Common causes |
|------|--------|---------------|
| 1 | Unknown symbol | Invalid margin market ticker |
| 2 | Exchange closed | Trading paused or unavailable |
| 3 | Order exceeds limit | Risk limit breach or insufficient margin |
| 4 | Too late to enter | Market not accepting new orders |
| 5 | Stale order | Expired timestamp on request |
| 6 | Duplicate order | `ClOrdID` already used |
| 11 | Unsupported order characteristic | Invalid order parameters |
| 13 | Incorrect quantity | Invalid order size |
| 15 | Unknown account | Subaccount not found or permission denied |
| 99 | Other | See `Text` field |

#### Cancel Reject Reasons (`102`)

In `OrderCancelReject (35=9)`:

| Code | Reason | Description |
|------|--------|-------------|
| 0 | Too late to cancel | Order already filled |
| 1 | Unknown order | Order not found or identifiers do not match |
| 99 | Other | See `Text` field |

### Common error scenarios

**Invalid tag**
```text
// Sent
8=FIXT.1.1|35=D|11=123|38=10|333333=test|...

// Response: Reject
8=FIXT.1.1|35=3|45=5|58=Undefined tag received|371=333333|372=D|373=3|
```

**Order rejected by exchange**
```text
// Sent
8=FIXT.1.1|35=D|11=456|38=10|55=BTC-PERP|44=19.5000|...

// Response: ExecutionReport (Rejected)
8=FIXT.1.1|35=8|11=456|150=8|39=8|58=EXCHANGE_PAUSED|103=2|...
```

Exchange order-entry failures are sent as `ExecutionReport` with `ExecType=Rejected`, **not** `BusinessMessageReject`. `BusinessMessageReject` is used for application-layer failures before normal exchange rejection handling, such as rate limiting or listener-session restrictions.

**Insufficient balance**
```text
// Response: ExecutionReport
8=FIXT.1.1|35=8|11=789|150=8|39=8|58=INSUFFICIENT_BALANCE|103=3|...
```

### Troubleshooting

**`MsgSeqNum` too high on Logon**
- Symptom: Logon fails or server sends `ResendRequest` for messages the client does not have.
- Cause: client `MsgSeqNum` higher than server last saw. Typically local sequence store persisted across sessions but server reset (maintenance or prior `ResetSeqNumFlag=Y`).
- Fix:
  - `KalshiNR` / `KalshiDC`: set `ResetSeqNumFlag<141>=Y` on every Logon (required; Logon rejected without it).
  - `KalshiRT`: if recovery is not needed, set `ResetSeqNumFlag<141>=Y` to reset both sides to 1. If retransmission continuity is needed, keep local sequence store in sync with server state.
- QuickFIX users: set `ResetOnLogon=Y` for non-retransmission sessions.

**`SendingTime` rejected**
- Symptom: `Reject (35=3)` with `SessionRejectReason<373>=10`.
- Cause: client clock >30 seconds off server time.
- Fix: sync system clock via NTP.

**Duplicate session (“already exists”)**
- Symptom: `Logout (35=5)` immediately after Logon with `Text<58>="already exists"`.
- Cause: another FIX connection is already active with same API key + TargetCompID. Only one connection allowed per API key per session type. May also occur if a previous connection was not cleanly closed and the server has not yet detected the disconnect.
- Fix: ensure previous session fully disconnected before reconnecting. If lost unexpectedly, wait for server heartbeat timeout (up to 60 seconds depending on `HeartbeatInt`) before retrying. Use separate API keys for concurrent connections.

**Logon signature rejected**
- Symptom: `Logout` immediately after Logon with a signature error.
- Cause: `SendingTime` used in the pre-hash string does not match `SendingTime<52>` in the actual Logon message. If using a FIX library that auto-populates `SendingTime`, use that exact value when computing the signature, not a separately generated timestamp.
