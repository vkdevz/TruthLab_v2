from pathlib import Path
from PIL import Image, ExifTags
from typing import Any, Dict


class MetadataForensics:
    """Inspects EXIF metadata, camera provenance, editing software tags, dimensions,
    timestamps, and C2PA content credentials without assuming missing EXIF implies tampering."""

    def analyze(self, image_path: Path | str) -> dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            return {
                "has_exif": False,
                "software_tag": None,
                "c2pa_present": False,
                "dimensions": None,
                "format": None,
                "color_mode": None,
                "timestamps": [],
                "camera_make": None,
                "camera_model": None,
                "notes": ["File not found"],
            }

        notes = []
        has_exif = False
        software_tag = None
        c2pa_present = False
        dimensions = None
        img_format = None
        color_mode = None
        timestamps = []
        camera_make = None
        camera_model = None

        try:
            with Image.open(path) as img:
                dimensions = {"width": img.width, "height": img.height}
                img_format = img.format
                color_mode = img.mode

                exif_data = img.getexif()
                if exif_data:
                    has_exif = True
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        val_str = str(value).strip()

                        if tag_name == "Software":
                            software_tag = val_str
                            notes.append(f"Editing software tag detected: {software_tag}")
                        elif tag_name == "Make":
                            camera_make = val_str
                        elif tag_name == "Model":
                            camera_model = val_str
                            notes.append(f"Camera device recorded: {val_str}")
                        elif "Date" in tag_name or "Time" in tag_name:
                            timestamps.append(f"{tag_name}: {val_str}")

                # Check raw binary header for C2PA or common generative model signatures
                with open(path, "rb") as f:
                    raw_header = f.read(8192)
                    if b"c2pa" in raw_header or b"jumbf" in raw_header:
                        c2pa_present = True
                        notes.append("Content Credentials / C2PA provenance manifest detected.")
                    if (
                        b"StableDiffusion" in raw_header
                        or b"DreamStudio" in raw_header
                        or b"Midjourney" in raw_header
                    ):
                        notes.append("Generative AI metadata tag detected in binary header.")

        except Exception as exc:
            notes.append(f"EXIF parsing warning: {str(exc)}")

        if not has_exif:
            notes.append(
                "Standard camera EXIF metadata absent (standard consequence of social media platform compression and re-encoding; not evidence of forgery)."
            )

        return {
            "has_exif": has_exif,
            "software_tag": software_tag,
            "c2pa_present": c2pa_present,
            "dimensions": dimensions,
            "format": img_format,
            "color_mode": color_mode,
            "timestamps": timestamps,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "notes": notes,
        }


metadata_forensics = MetadataForensics()

