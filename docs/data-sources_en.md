# Data Sources

[中文](./data-sources.md) | [English](./data-sources_en.md)

The project combines multiple public sources instead of depending on a single vendor.

## Overview

| Source | Main use | Access | Notes |
|---|---|---|---|
| Tencent Finance | Quotes, daily and minute K-lines | HTTP | Primary market-data entry |
| Sina Finance | Financial statements | HTTP | Shanghai/Shenzhen equities |
| CNINFO | Company announcements | HTTP | Shanghai/Shenzhen/Beijing disclosures |
| Eastmoney | Profiles, research, margin data, block trades, holder count, dividends, fund flow | HTTP | Serialized rate-aware access |
| baostock | Historical valuation and listing basics | Python client | Optional dependency; no Beijing coverage |
| NBS | PMI | Official website | Parses latest release |
| SSE | ETF PCF and regulatory events | Official interface / XML | Source evidence retained |
| HKEX | Stock Connect eligibility lists | Official CSV | Eligible and sell-only lists |

## Source strategy

### Tencent for core market data

Quotes and K-lines are exposed through a dedicated Tencent provider so the most frequently used market-data path does not depend on the same source as specialized datasets.

### CNINFO for disclosures

Announcement queries return normalized metadata, detail pages, and downloadable attachments where available.

### Eastmoney for specialized research datasets

The Eastmoney provider covers:

- company profiles;
- stock and industry research reports;
- margin trading;
- block trades;
- shareholder count;
- dividends;
- historical fund-flow data.

Requests use a serialized `RateLimitedSession`.

### Evidence fields for official datasets

Official files and lists retain fields such as:

- `source`
- `source_url`
- `fetched_at`
- `content_sha256`

This makes them more suitable for archival and event-research workflows.

## Known limitations

- Public interfaces can change without notice.
- Some Eastmoney endpoints can behave differently across network environments.
- baostock does not currently cover Beijing Stock Exchange symbols.
- Tencent K-line support for Beijing-listed securities is not treated as reliable in the current implementation.
- The NBS PMI parser depends on the structure of the latest-release page.

When an upstream schema changes, the library prefers an explicit error over a misleading empty result.