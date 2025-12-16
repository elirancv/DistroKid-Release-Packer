const fs = require('fs');
const path = require('path');

function renameAudioFiles(artist, title, sourceDir, destDir, overwrite = false) {
  if (!fs.existsSync(sourceDir)) {
    throw new Error(`Source directory not found: ${sourceDir}`);
  }
  
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }
  
  const files = fs.readdirSync(sourceDir);
  const audioFiles = files.filter(f => 
    f.endsWith('.wav') || f.endsWith('.mp3')
  );
  
  if (audioFiles.length === 0) {
    console.log(`⚠️  No audio files found in ${sourceDir}`);
    return;
  }
  
  audioFiles.forEach(file => {
    const ext = path.extname(file);
    const newName = `${artist} - ${title}${ext}`;
    
    const sourcePath = path.join(sourceDir, file);
    const destPath = path.join(destDir, newName);
    
    // Check for existing file
    if (fs.existsSync(destPath) && !overwrite) {
      throw new Error(
        `File already exists: ${destPath}\n` +
        `  To overwrite, set 'overwrite_existing: true' in release.json`
      );
    }
    
    fs.copyFileSync(sourcePath, destPath);
    console.log(`✓ Renamed: ${newName}`);
  });
}

// Usage
if (require.main === module) {
  renameAudioFiles('Your Artist', 'Your Title', './exports', './Releases/TrackName/Audio');
}

module.exports = { renameAudioFiles };

