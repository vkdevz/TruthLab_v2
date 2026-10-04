from datetime import datetime, timezone
from backend.app.schemas.temporal import TemporalVerificationResult
from backend.app.schemas.claim import AtomicClaim
from backend.app.schemas.evidence import EvidenceSnippet
from backend.app.ml.context.temporal_parser import temporal_parser
from backend.app.ml.context.geolocation_matcher import geolocation_matcher
from backend.app.core.config import settings


class TemporalVerifier:
    """Detects temporal anachronisms, outdated recycled news, and geolocation mismatches."""

    def verify_context(
        self,
        claim: AtomicClaim,
        evidence_items: list[EvidenceSnippet]
    ) -> TemporalVerificationResult:
        notes = []
        is_outdated = False
        is_anachronistic = False

        # 1. Parse claim date and urgency framing
        present_framing = temporal_parser.has_present_framing(claim.raw_text)
        claim_anchor, claim_date = temporal_parser.parse_text_timestamp(claim.raw_text)

        if not claim_date and claim.inferred_date:
            claim_date = claim.inferred_date.replace(tzinfo=timezone.utc)
            claim_anchor = claim.temporal_anchor

        # 2. Extract earliest and latest evidence publication dates
        valid_ev_dates = [
            ev.publication_date.replace(tzinfo=timezone.utc)
            for ev in evidence_items
            if ev.publication_date is not None
        ]

        delta_days = None
        ev_date = None

        if valid_ev_dates:
            ev_date = min(valid_ev_dates)  # Original occurrence date
            now = datetime.now(timezone.utc)

            # Compare against current time if claim asserts present urgency
            if present_framing:
                delta_days = abs((now - ev_date).days)
                if delta_days > settings.TEMPORAL_OUTDATED_DAYS:
                    is_outdated = True
                    notes.append(
                        f"Temporal recycling detected: claim presents event with current/breaking urgency, "
                        f"but evidence indicates this event occurred {delta_days} days ago ({ev_date.strftime('%Y-%m-%d')})."
                    )
            elif claim_date:
                delta_days = abs((claim_date - ev_date).days)
                if delta_days > settings.TEMPORAL_OUTDATED_DAYS:
                    is_anachronistic = True
                    notes.append(
                        f"Timeline mismatch: claim asserts date {claim_date.strftime('%Y-%m-%d')}, "
                        f"but verified evidence occurred on {ev_date.strftime('%Y-%m-%d')} (delta: {delta_days} days)."
                    )

        # 3. Spatial geolocation verification
        snippet_texts = [ev.snippet_text for ev in evidence_items]
        loc_status, loc_notes = geolocation_matcher.check_consistency(claim.raw_text, snippet_texts)
        notes.extend(loc_notes)

        return TemporalVerificationResult(
            claim_anchor=claim_anchor,
            claim_date=claim_date,
            evidence_date=ev_date,
            delta_days=delta_days,
            is_outdated=is_outdated,
            is_anachronistic=is_anachronistic,
            present_framing_detected=present_framing,
            location_match_status=loc_status,
            temporal_notes=notes,
        )


temporal_verifier = TemporalVerifier()
