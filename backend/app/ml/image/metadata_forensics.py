from pathlib import Path
from PIL import Image, ExifTags


class MetadataForensics:
    """Inspects EXIF metadata, camera provenance, editing software tags, and C2PA credentials."""

    def analyze(self, image_path: Path | str) -> dict[str, any]:
        path = Path(image_path)
        if not path.exists():
            return {"has_exif": False, "software_tag": None, "c2pa_present": False, "notes": ["File not found"]}

        notes = []
        has_exif = False
        software_tag = None
        c2pa_present = False

        try:
            with Image.open(path) as img:
                exif_data = img.getexif()
                if exif_data:
                    has_exif = True
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if tag_name == "Software":
                            software_tag = str(value)
                            notes.append(f"Editing software tag detected: {software_tag}")
                        elif tag_name == "Model":
                            notes.append(f"Camera model recorded: {value}")

                # Check raw bytes for C2PA or common generative model headers
                with open(path, "rb") as f:
                    raw_header = f.read(8192)
                    if b"c2pa" in raw_header or b"jumbf" in raw_header:
                        c2pa_present = True
                        notes.append("Content Credentials / C2PA provenance manifest detected.")
                    if b"StableDiffusion" in raw_header or b"DreamStudio" in raw_header or b"Midjourney" in raw_header:
                        notes.append("Generative AI metadata tag detected in binary header.")

        except Exception as exc:
            notes.append(f"EXIF parsing warning: {str(exc)}")

        if not has_exif:
            notes.append("No standard camera EXIF metadata found (typical for web/social media compressed images).")

        return {
            "has_exif": has_exif,
            "software_tag": software_tag,
            "c2pa_present": c2pa_present,
            "notes": notes,
        }


metadata_forensics = MetadataForensics()
