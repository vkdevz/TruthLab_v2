from backend.app.schemas.media import ImageForensicIndicators, VideoForensicIndicators


class CrossModalAlignmentChecker:
    """Evaluates semantic consistency between visual signals (OCR text, media authenticity)
    and textual claims to detect 'cheapfakes' and out-of-context caption mismatches."""

    def compute_alignment(
        self,
        claim_text: str,
        ocr_text: str | None = None,
        image_forensics: ImageForensicIndicators | None = None,
        video_forensics: VideoForensicIndicators | None = None,
    ) -> tuple[float, list[str]]:
        notes = []
        alignment_score = 1.0  # Base assumption: aligned

        # 1. OCR vs Claim alignment (if visual text is present)
        if ocr_text and len(ocr_text.strip()) > 5:
            c_words = set(claim_text.lower().split())
            ocr_words = set(ocr_text.lower().split())
            intersection = c_words.intersection(ocr_words)
            union = c_words.union(ocr_words)
            jaccard = len(intersection) / len(union) if union else 0.0

            if jaccard < 0.10 and len(ocr_words) >= 4:
                alignment_score -= 0.45
                notes.append(
                    "Cross-modal disparity: textual claim differs significantly from the visual text displayed inside the image."
                )
            else:
                notes.append("Visual text on screen is semantically congruent with the textual claim.")

        # 2. Synthetic media mismatch
        if image_forensics and image_forensics.synthetic_probability > 0.75:
            alignment_score -= 0.25
            notes.append("Elevated synthetic image probability reduces cross-modal evidentiary reliability.")

        # 3. Visual tampering / Splicing
        if image_forensics and image_forensics.is_ela_spliced:
            alignment_score -= 0.30
            notes.append("Localized visual splicing detected via ELA, indicating image alteration.")

        clamped = float(round(max(0.05, min(1.0, alignment_score)), 3))
        return clamped, notes


cross_modal_alignment = CrossModalAlignmentChecker()
