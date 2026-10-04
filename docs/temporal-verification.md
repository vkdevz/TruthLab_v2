# Temporal & Context Verification

## 1. Overview
Temporal reasoning is a core capability for detecting misinformation. Misinformation frequently re-circulates real historical footage or outdated news stories and presents them as breaking or current events (out-of-context recycling or cheapfakes).

The Temporal Verifier (`temporal_verifier.py`) decouples:
- **Event Date**: When the event actually occurred (extracted from claim text and evidence snippets).
- **Source Publication Date**: When the article or source was published.
- **Reference Date**: The reference timestamp (e.g. today / verification time).

---

## 2. Temporal Status Classification

The system classifies temporal alignment into four discrete states:

| Status | Definition | Example | Verdict Impact |
| :--- | :--- | :--- | :--- |
| `CURRENT` | Claim describes an event whose occurrence matches recent evidence. | "New inflation report released this morning" corroborated by today's economic release. | Allowed to resolve to `SUPPORTED` if evidence matches. |
| `HISTORICAL` | Claim discusses past events in proper past context without pretending they are breaking. | "Apollo 11 landed on the Moon in 1969" corroborated by a retrospective written in 2019. | Not penalized; resolves to `SUPPORTED` based on factual accuracy. |
| `OUTDATED` | Genuine historical event presented as breaking, immediate, or current news. | "Massive earthquake hits Tokyo today" paired with footage from 2011. | Penalized with high temporal penalty; resolves to `OUTDATED`. |
| `UNKNOWN` | Neither claim nor evidence contains sufficient dates to determine temporal alignment. | "The government voted to ban electric scooters." | Preserves uncertainty; does not guess dates. |

---

## 3. Date Extraction & Decoupling

### 3.1 Event Date Extraction from Evidence
Evidence articles often report on past events years after they occurred (e.g., an article published in 2021 describing an event in 2014). To avoid falsely penalizing historical claims:
1. Regex and NLP temporal parsers scan the evidence snippet text for explicit event years and date expressions (e.g. `"in July 1969"`, `"on March 11, 2011"`).
2. If an event date is found inside the text, it takes precedence over the publication date of the article.

### 3.2 Urgency & Recency Markers
Claims with breaking news markers:
- `"breaking"`, `"today"`, `"right now"`, `"just in"`, `"live"`, `"yesterday"`
When paired with evidence whose event date or source date is over 365 days in the past, the temporal consistency score drops and triggers `is_outdated = True`.

---

## 4. Geographic Context Consistency (`geolocation_matcher.py`)
- Analyzes mentioned locations in claims (e.g., countries, cities, regions).
- Compares claimed locations against evidence source locations and entities.
- If no geographic entities are identifiable in either claim or evidence, the layer returns `UNKNOWN` rather than guessing.
