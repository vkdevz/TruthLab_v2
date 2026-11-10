from datetime import datetime, timezone
import re
from backend.app.schemas.temporal import TemporalVerificationResult
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.ml.context.temporal_parser import temporal_parser
from backend.app.ml.context.geolocation_matcher import geolocation_matcher
from backend.app.core.config import settings


class TemporalVerifier:
    """Evaluates temporal semantics: separates event date from publication date,
    detects temporal recycling / outdated claims, and verifies geographic consistency
    without treating missing dates as an automatic fault."""

    def extract_event_date_from_evidence(
        self, evidence_items: list[EvidenceSnippet]
    ) -> tuple[datetime | None, str | None]:
        """Heuristically extracts the actual occurrence date of the underlying event
        from evidence snippets, avoiding naive conflation with article publication date."""
        for ev in evidence_items:
            text = ev.snippet_text
            # 1. Look for explicit event past markers e.g. "happened in 2020", "originally occurred on March 14, 2019"
            match = re.search(r"(?:originally\s+(?:occurred|happened|taken|filmed|recorded)\s+(?:in|on)\s+)([A-Za-z0-9\s,]+)", text, re.I)
            if match:
                phrase = match.group(1).strip()
                anchor, dt = temporal_parser.parse_text_timestamp(phrase)
                if dt:
                    return dt, f"Event occurrence date identified from evidence context: {phrase}"

            # 2. Look for any explicit year/date in the evidence text itself
            anchor, dt = temporal_parser.parse_text_timestamp(text)
            if dt:
                return dt, f"Historical date '{anchor}' corroborated directly within evidence text."

        # If no explicit event marker is found in snippet text, look at claim reviews
        for ev in evidence_items:
            if ev.is_claim_review and ev.publication_date:
                # Fact-checks often date the hoax or the original occurrence
                return ev.publication_date.replace(tzinfo=timezone.utc), "Event date estimated from fact-check investigation date."

        return None, None


    def verify_context(
        self,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet]
    ) -> TemporalVerificationResult:
        notes = []
        is_outdated = False
        is_anachronistic = False
        temporal_status = "UNKNOWN"
        reason = None

        now = datetime.now(timezone.utc)

        # 1. Parse claim assertions
        present_framing = temporal_parser.has_present_framing(claim.raw_text)
        claim_anchor, claim_date = temporal_parser.parse_text_timestamp(claim.raw_text)

        if not claim_date and claim.inferred_date:
            claim_date = claim.inferred_date.replace(tzinfo=timezone.utc)
            claim_anchor = claim.temporal_anchor

        # 2. Extract publication dates of evidence sources
        valid_pub_dates = [
            ev.publication_date.replace(tzinfo=timezone.utc)
            for ev in evidence_items
            if ev.publication_date is not None
        ]
        earliest_source_date = min(valid_pub_dates) if valid_pub_dates else None

        # 3. Extract actual event date (distinguished from publication date)
        event_date, event_date_note = self.extract_event_date_from_evidence(evidence_items)
        if event_date_note:
            notes.append(event_date_note)

        # Fallback to source date if event date is not explicitly mentioned in text
        effective_event_date = event_date or earliest_source_date

        delta_days = None

        # 4. Temporal reasoning
        if present_framing:
            if effective_event_date:
                delta_days = abs((now - effective_event_date).days)
                if delta_days > settings.TEMPORAL_OUTDATED_DAYS:
                    is_outdated = True
                    temporal_status = "OUTDATED"
                    reason = (
                        f"Temporal recycling: statement presents event with breaking/current urgency, "
                        f"but underlying occurrence dates back {delta_days} days to {effective_event_date.strftime('%Y-%m-%d')}."
                    )
                    notes.append(reason)
                else:
                    temporal_status = "CURRENT"
                    reason = f"Event framing aligns with recent occurrence ({delta_days} days ago)."
            else:
                temporal_status = "CURRENT"
                reason = "Present-tense framing without older historical occurrence records found."

        elif claim_date:
            if effective_event_date:
                is_year_only = bool(claim_anchor and claim_anchor.isdigit() and len(claim_anchor) == 4)
                if is_year_only and claim_date.year == effective_event_date.year:
                    temporal_status = "HISTORICAL" if claim_date.year < now.year else "CURRENT"
                    reason = f"Explicit year {claim_anchor} aligns with historical event year ({effective_event_date.year})."
                else:
                    delta_days = abs((claim_date - effective_event_date).days)
                    if delta_days > settings.TEMPORAL_OUTDATED_DAYS:
                        is_anachronistic = True
                        temporal_status = "OUTDATED"
                        reason = (
                            f"Timeline mismatch: claim specifies {claim_date.strftime('%Y-%m-%d')}, "
                            f"whereas verified records place the event on {effective_event_date.strftime('%Y-%m-%d')} (delta: {delta_days} days)."
                        )
                        notes.append(reason)
                    else:
                        temporal_status = "HISTORICAL" if claim_date.year < now.year else "CURRENT"
                        reason = f"Explicit date {claim_date.strftime('%Y-%m-%d')} aligns with historical records."
            else:
                temporal_status = "HISTORICAL" if claim_date.year < now.year else "CURRENT"
                reason = f"Claim references explicit date ({claim_date.strftime('%Y-%m-%d')})."

        elif effective_event_date:
            delta_days = abs((now - effective_event_date).days)
            if delta_days > 730:
                temporal_status = "HISTORICAL"
                reason = f"Underlying event occurred historically on {effective_event_date.strftime('%Y-%m-%d')}."
            else:
                temporal_status = "CURRENT"
                reason = f"Event verified to recent timeframe ({effective_event_date.strftime('%Y-%m-%d')})."
        else:
            temporal_status = "UNKNOWN"
            reason = "No verifiable timestamp or historical anchor found in claim or evidentiary sources."

        # 5. Spatial geolocation consistency
        snippet_texts = [ev.snippet_text for ev in evidence_items]
        loc_status, loc_notes = geolocation_matcher.check_consistency(claim.raw_text, snippet_texts)
        notes.extend(loc_notes)

        return TemporalVerificationResult(
            temporal_status=temporal_status,
            claim_anchor=claim_anchor,
            claim_date=claim_date,
            event_date=effective_event_date,
            source_date=earliest_source_date,
            evidence_date=effective_event_date,
            reference_date=now,
            delta_days=delta_days,
            is_outdated=is_outdated,
            is_anachronistic=is_anachronistic,
            present_framing_detected=present_framing,
            reason=reason,
            location_match_status=loc_status,
            temporal_notes=notes,
        )


temporal_verifier = TemporalVerifier()

