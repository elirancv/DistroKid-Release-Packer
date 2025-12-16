# ID3 Tagging Standards for DistroKid (2025)

Complete guide to ID3 tags required, recommended, and optional for DistroKid releases.

## Important Note

**DistroKid does not rely on embedded ID3 tags** - it uses form metadata from their web interface. However, properly tagged files are critical for:

- ✅ Apple Music ingestion safety
- ✅ File portability
- ✅ Archives, DJs, radio, promo pools
- ✅ Re-uploads, migrations, takedowns
- ✅ Avoiding conflicts with DistroKid metadata

---

## 1. ABSOLUTE MUST-HAVE TAGS (Minimum Viable)

These should **always** be present in your MP3 files.

| Tag | ID3 Frame | Required | Notes |
|-----|-----------|----------|-------|
| **Track Title** | TIT2 | ✅ | Must match DistroKid title exactly |
| **Artist** | TPE1 | ✅ | Main artist only |
| **Album / Release Title** | TALB | ✅ | Single = single title |
| **Track Number** | TRCK | ✅ | Format: `1/1`, `2/5`, etc. |
| **Year** | TYER / TDRC | ✅ | Use release year |
| **Genre** | TCON | ✅ | One clean genre only |
| **Artwork** | APIC | ✅ | Embedded JPG (same as cover.jpg) |

**Tool Status:** ✅ **All automatically applied**

---

## 2. STRONGLY RECOMMENDED (Professional Standard)

These reduce rejection risk and improve DSP ingestion quality.

| Tag | ID3 Frame | Why It Matters | Tool Status |
|-----|-----------|----------------|-------------|
| **Album Artist** | TPE2 | Prevents compilation issues | ✅ **Auto-set to artist if not specified** |
| **Composer** | TCOM | Required by Apple Music logic | ✅ **Auto-generated from template** |
| **Publisher / Label** | TPUB | Even "Self-Released" | ✅ **Auto-set from artist-defaults.json** |
| **Copyright** | TCOP | Ownership clarity | ✅ **Auto-generated: © YEAR ARTIST** |
| **BPM** | TBPM | DJ / catalog systems | ✅ **Auto-set from config.bpm** |
| **ISRC** | TSRC | DistroKid will generate, but archive it | ✅ **Auto-set from config.isrc** |
| **Encoder** | TSSE | Transparency | ✅ **Auto-set: "DistroKid Release Packer"** |
| **Language** | TLAN | Especially for non-English lyrics | ✅ **Auto-set from config.language** |

**Tool Status:** ✅ **All automatically applied when available**

---

## 3. OPTIONAL BUT HIGH-VALUE (Archive-Grade)

Use these if you want future-proof, enterprise-level metadata.

| Tag | ID3 Frame | Use Case | Tool Status |
|-----|-----------|----------|-------------|
| **Lyrics** | USLT | Apple Music, Spotify lyrics sync | ❌ Not implemented |
| **Comment** | COMM | Internal notes | ✅ **Auto-set with Suno version info** |
| **Grouping** | TIT1 | DJ sets, collections | ❌ Not implemented |
| **Mood** | TMOO | Catalog & AI tools | ❌ Not implemented |
| **Media Type** | TMED | Digital / Streaming | ❌ Not implemented |
| **Original Artist** | TOPE | Covers, remixes | ❌ Not implemented |
| **Original Release Year** | TDOR | Re-issues | ❌ Not implemented |
| **URL (Official)** | WOAR | Artist website | ❌ Not implemented |
| **Commercial URL** | WCOM | Store page | ❌ Not implemented |

---

## 4. TAGS YOU SHOULD NOT USE

These cause confusion or rejections downstream.

❌ **Multiple genres** - Use one clean genre only  
❌ **Emojis in any text field** - Use plain text  
❌ **Promo text** (OUT NOW, FREE) - Keep titles clean  
❌ **Store names** (Spotify, Apple Music) - Not allowed  
❌ **Different artwork embedded than uploaded** - Must match  
❌ **Version info in title** - Use DistroKid fields instead  

**Tool Status:** ✅ **Tool prevents these issues**

---

## 5. GOLD-STANDARD SINGLE TRACK TAG SET (Example)

```
TIT2  = European Dancefloor Meditation  (Track Title)
TPE1  = Jimi Jules                       (Artist)
TPE2  = Jimi Jules                       (Album Artist)
TALB  = European Dancefloor Meditation  (Album)
TRCK  = 1/1                              (Track Number)
TDRC  = 2025                             (Year)
TCON  = Organic House                    (Genre)
TCOM  = Jimi Jules                       (Composer)
TPUB  = Self-Released                    (Publisher)
TCOP  = © 2025 Jimi Jules                (Copyright)
TBPM  = 122                              (BPM)
TSRC  = USRC176078234                    (ISRC - if available)
TSSE  = DistroKid Release Packer         (Encoder)
TLAN  = eng                              (Language)
APIC  = cover.jpg                        (Artwork)
COMM  = AI-generated with Suno, v3.5.2   (Comment)
```

**This is 100% safe for all DSPs.**

---

## 6. How the Tool Handles ID3 Tags

### Automatic Tagging

The tool automatically applies **all required and recommended tags**:

1. **Required tags** - Always set from config
2. **Album Artist (TPE2)** - Auto-set to artist if not specified
3. **Copyright (TCOP)** - Auto-generated: `© YEAR ARTIST`
4. **BPM (TBPM)** - Auto-set from `config.bpm`
5. **ISRC (TSRC)** - Auto-set from `config.isrc` if available
6. **Language (TLAN)** - Auto-set from `config.language` with ISO code mapping
7. **Encoder (TSSE)** - Auto-set to "DistroKid Release Packer"
8. **Comment (COMM)** - Auto-includes Suno version info

### Configuration

**In `release.json`:**
```json
{
  "bpm": 122,
  "language": "English",
  "isrc": "USRC176078234",
  "id3_metadata": {
    "album": "Summer Vibes EP",
    "year": "2025",
    "tracknumber": "1/5",
    "composer": "YourArtistName + Suno AI",
    "publisher": "Independent",
    "album_artist": "YourArtistName",
    "copyright": "© 2025 YourArtistName"
  }
}
```

**In `artist-defaults.json` (defaults):**
```json
{
  "default_publisher": "Independent",
  "default_composer_template": "{artist} + Suno AI"
}
```

---

## 7. Verification

After running the tool, verify tags with:

**Python:**
```python
from mutagen.easyid3 import EasyID3
audio = EasyID3("your-file.mp3")
print(audio.keys())  # See all tags
```

**Or use a tag editor:**
- MP3Tag (Windows/Mac)
- MusicBrainz Picard
- Kid3

---

## 8. Important Truth

**ID3 tags do NOT override DistroKid metadata.**  
DistroKid's web form is the source of truth.

However:
- ✅ Bad ID3 tags can conflict
- ✅ Missing ID3 tags can break archives
- ✅ Clean tags = painless re-uploads & migrations

**The tool ensures your files are properly tagged for maximum compatibility and future-proofing.**

