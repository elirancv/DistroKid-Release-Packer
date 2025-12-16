import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs


def extract_suno_version_from_url(url):
    """Extract Suno version and build ID from track URL."""
    parsed = urlparse(url)

    # Extract from path (e.g., /song/abc123xyz)
    path_match = re.search(r"/song/([a-zA-Z0-9_-]+)", parsed.path)
    track_id = path_match.group(1) if path_match else None

    # Extract from query params
    params = parse_qs(parsed.query)
    version = params.get("v", [None])[0]
    build_id = params.get("build", [None])[0]

    return {"track_id": track_id, "version": version, "build_id": build_id, "url": url}


def extract_from_metadata_file(metadata_path):
    """Extract version info from saved Suno metadata JSON."""
    metadata_file = Path(metadata_path)

    if not metadata_file.exists():
        print(f"✗ Metadata file not found: {metadata_path}")
        return None

    try:
        with open(metadata_file, "r") as f:
            data = json.load(f)
            return {
                "version": data.get("version"),
                "build_id": data.get("build_id") or data.get("id"),
                "created_at": data.get("created_at"),
                "model_version": data.get("model_version"),
            }
    except Exception as e:
        print(f"✗ Error reading metadata: {e}")
        return None


if __name__ == "__main__":
    # Usage example
    url = "https://suno.com/song/abc123xyz?v=3.5.2&build=xyz789"
    version_info = extract_suno_version_from_url(url)
    print(json.dumps(version_info, indent=2))
