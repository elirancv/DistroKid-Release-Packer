const NodeID3 = require('node-id3');
const fs = require('fs');
const path = require('path');

function tagAudioFile(audioPath, coverPath, metadata) {
  if (!fs.existsSync(audioPath)) {
    throw new Error(`Audio file not found: ${audioPath}`);
  }
  
  const ext = path.extname(audioPath).toLowerCase();
  if (ext !== '.mp3') {
    throw new Error(`Invalid format: ${ext}. Only MP3 supported`);
  }
  
  // Read cover art
  let coverImage = null;
  if (coverPath && fs.existsSync(coverPath)) {
    coverImage = fs.readFileSync(coverPath);
  } else if (coverPath) {
    console.log(`⚠️  Cover art file not found: ${coverPath}`);
  }
  
  // Prepare ID3 tags (DistroKid 2025 Standard)
  // REQUIRED TAGS
  const tags = {
    title: metadata.title || '',  // TIT2
    artist: metadata.artist || '',  // TPE1
    album: metadata.album || '',  // TALB
    genre: metadata.genre || '',  // TCON
    year: metadata.year || '',  // TYER/TDRC
    trackNumber: metadata.tracknumber || '1',  // TRCK
    composer: metadata.composer || '',  // TCOM (Strongly Recommended)
    albumArtist: metadata.album_artist || metadata.artist || '',  // TPE2 (Strongly Recommended)
    publisher: metadata.publisher || 'Independent',  // TPUB (Strongly Recommended)
    copyright: metadata.copyright || (metadata.artist && metadata.year ? `© ${metadata.year} ${metadata.artist}` : undefined),  // TCOP (Strongly Recommended)
    bpm: metadata.bpm ? String(metadata.bpm) : undefined,  // TBPM (Strongly Recommended)
    ISRC: metadata.isrc || undefined,  // TSRC (Strongly Recommended)
    // Encoder (TSSE) - Optional metadata only (NOT a DistroKid requirement)
    // Only add if explicitly provided
    encoder: metadata.encoder || undefined,  // Optional - only tag if provided
    language: metadata.language_code || metadata.language || undefined,  // TLAN (Strongly Recommended)
    comment: metadata.comment ? {
      language: 'eng',
      text: metadata.comment
    } : undefined,
    image: coverImage ? {
      mime: coverPath.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg',
      type: { id: 3, name: 'front cover' },
      description: 'Cover',
      imageBuffer: coverImage
    } : undefined
  };
  
  // Remove undefined values to avoid issues
  Object.keys(tags).forEach(key => {
    if (tags[key] === undefined) {
      delete tags[key];
    }
  });
  
  // Write tags
  const success = NodeID3.write(tags, audioPath);
  
  if (success) {
    console.log(`✓ ID3v2 tags applied successfully: ${path.basename(audioPath)}`);
    return true;
  } else {
    console.error(`✗ Failed to tag: ${audioPath}`);
    return false;
  }
}

function batchTagFiles(sourceDir, destDir, coverPath, metadataTemplate) {
  if (!fs.existsSync(sourceDir)) {
    throw new Error(`Source directory not found: ${sourceDir}`);
  }
  
  const files = fs.readdirSync(sourceDir);
  const mp3Files = files.filter(f => f.endsWith('.mp3'));
  
  if (mp3Files.length === 0) {
    console.log(`⚠️  No MP3 files found in ${sourceDir}`);
    return;
  }
  
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }
  
  mp3Files.forEach((file, index) => {
    const sourcePath = path.join(sourceDir, file);
    const destPath = path.join(destDir, file);
    
    // Copy file
    fs.copyFileSync(sourcePath, destPath);
    
    // Create metadata for this file
    const metadata = { ...metadataTemplate };
    metadata.tracknumber = String(index + 1);
    
    // Tag the copied file
    tagAudioFile(destPath, coverPath, metadata);
  });
  
  console.log(`✓ Tagged ${mp3Files.length} files`);
}

// Usage Example
if (require.main === module) {
  const metadata = {
    title: 'Deep Dive',
    artist: 'YourArtistName',
    album: 'Summer Vibes EP',
    genre: 'Deep House',
    year: '2025',
    tracknumber: '1',
    composer: 'YourArtistName + Suno AI',
    publisher: 'Independent',
    comment: 'AI-generated with Suno, v3.5.2, Build abc123xyz'
  };
  
  tagAudioFile(
    'YourArtistName - Deep Dive.mp3',
    'cover.jpg',
    metadata
  );
}

module.exports = { tagAudioFile, batchTagFiles };

