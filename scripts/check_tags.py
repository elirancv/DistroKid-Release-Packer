#!/usr/bin/env python3
"""Quick script to check ID3 tags"""

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from pathlib import Path

files = list(Path("runtime/output/ThankYouLordNicolasJaarRMX/Audio").glob("*.mp3"))
if not files:
    print("No MP3 files found")
    exit(1)

audio_file = str(files[0])
print(f"Checking: {audio_file}\n")

# Check EasyID3 tags
audio = EasyID3(audio_file)
print("EasyID3 Tags:")
print(f"  Title: {audio.get('title', ['N/A'])[0]}")
print(f"  Artist: {audio.get('artist', ['N/A'])[0]}")
print(f"  Album: {audio.get('album', ['N/A'])[0]}")
print(f"  Composer: {audio.get('composer', ['N/A'])[0]}")
print(f"  Date: {audio.get('date', ['N/A'])[0]}")
print(f"  Track: {audio.get('tracknumber', ['N/A'])[0]}")

# Check low-level ID3 tags
audio_mp3 = MP3(audio_file, ID3=ID3)
print("\nAdditional ID3 Tags:")
if audio_mp3.tags:
    for tag in audio_mp3.tags.values():
        if tag.FrameID == "TPUB":
            print(f"  Publisher: {tag.text[0] if tag.text else 'N/A'}")
        elif tag.FrameID == "COMM":
            print(f"  Comment: {tag.text[0] if tag.text else 'N/A'}")
