# Audio Clipping Guide

## What is Clipping?

**Audio clipping** occurs when the audio signal exceeds the maximum digital level (0 dBFS or 1.0 in normalized audio). This causes distortion and can make your track sound harsh or distorted.

## Your Current Issue

**Detected:** Max amplitude: **0.9978** (threshold: 0.99)

Your audio is **very close to clipping** - samples are reaching 99.78% of maximum level. This is considered **hard clipping** and should be fixed before uploading to DistroKid.

## Why This Matters

- ❌ **DistroKid may reject** tracks with audible clipping
- ❌ **Streaming platforms** may apply additional limiting, making it worse
- ❌ **Poor listening experience** - harsh, distorted sound
- ❌ **Unprofessional** - indicates poor mastering

## How to Fix Clipping

### Option 1: Re-export from Suno (Recommended)

1. Go back to your Suno track
2. **Lower the volume/mastering level** before exporting
3. Aim for **-1 dB to -3 dB headroom** (max amplitude around 0.89-0.94)
4. Re-export the track
5. Run the tool again

### Option 2: Use Audio Software

**Free Options:**
- **Audacity** (Free, cross-platform)
  1. Open your MP3 file
  2. Select all (Ctrl+A)
  3. Effect → Amplify → Set to -1 dB or -2 dB
  4. Export as MP3

- **Reaper** (Free trial, professional)
  1. Import your track
  2. Add a limiter/compressor
  3. Set ceiling to -1 dB
  4. Export

**Online Tools:**
- **CloudConvert** - Audio normalization
- **AudioMass** - Web-based audio editor

### Option 3: Acceptable Levels

**Target levels for DistroKid:**
- ✅ **Ideal:** Max amplitude 0.89 - 0.94 (-1 dB to -0.5 dB headroom)
- ⚠️ **Acceptable:** Max amplitude 0.95 - 0.98 (near clipping, but not hard clipping)
- ❌ **Reject:** Max amplitude ≥ 0.99 (hard clipping detected)

## Current Status

Your track has **max amplitude: 0.9978** which is:
- ❌ **Above the 0.99 threshold** (hard clipping)
- ⚠️ **Needs fixing** before upload

## What the Tool Does

The tool **detects** clipping but **does not fix it**. You need to:
1. Fix the clipping in your source audio
2. Re-run the tool to verify it's fixed

## Quick Fix Command (if you have ffmpeg)

```bash
# Normalize to -1 dB (safe level)
ffmpeg -i "your-file.mp3" -af "volume=-1dB" "your-file-fixed.mp3"
```

## After Fixing

1. Replace the file in `exports/` directory
2. Set `"overwrite_existing": true` in `config.json`
3. Run the tool again: `python pack.py config.json`
4. Verify clipping check passes: `✅ PASSED` (no clipping detected)

---

**Remember:** It's better to have slightly quieter audio than clipped/distorted audio. Streaming platforms will normalize volume anyway.

