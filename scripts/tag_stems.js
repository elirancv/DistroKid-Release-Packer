const fs = require('fs');
const path = require('path');

function tagStemFile(stemPath, artist, title, stemType) {
  if (!fs.existsSync(stemPath)) {
    console.error(`✗ Stem file not found: ${stemPath}`);
    return false;
  }
  
  // For WAV files, create a companion JSON metadata file
  // (node-id3 works with MP3, not WAV)
  const metadata = {
    title: `${title} - ${stemType}`,
    artist: artist,
    album: title,
    genre: 'Stem',
    comment: {
      language: 'eng',
      text: `Stem type: ${stemType}`
    }
  };
  
  // Create companion JSON file
  const jsonPath = stemPath.replace('.wav', '.metadata.json');
  fs.writeFileSync(jsonPath, JSON.stringify(metadata, null, 2));
  
  console.log(`✓ Created metadata for stem: ${path.basename(stemPath)}`);
  return true;
}

function batchTagStems(stemsDir, artist, title) {
  if (!fs.existsSync(stemsDir)) {
    throw new Error(`Stems directory not found: ${stemsDir}`);
  }
  
  const files = fs.readdirSync(stemsDir);
  const stemFiles = files.filter(f => f.endsWith('.wav'));
  
  if (stemFiles.length === 0) {
    console.log(`⚠️  No WAV files found in ${stemsDir}`);
    return;
  }
  
  stemFiles.forEach(file => {
    const stemPath = path.join(stemsDir, file);
    const stemName = path.basename(file, '.wav');
    
    // Extract stem type from filename
    const parts = stemName.split(' - ');
    const stemType = parts.length >= 3 ? parts[parts.length - 1] : 'Unknown';
    
    tagStemFile(stemPath, artist, title, stemType);
  });
  
  console.log(`✓ Tagged ${stemFiles.length} stem files`);
}

// Usage
if (require.main === module) {
  batchTagStems('./Releases/DeepDive/Stems', 'YourArtistName', 'Deep Dive');
}

module.exports = { tagStemFile, batchTagStems };

