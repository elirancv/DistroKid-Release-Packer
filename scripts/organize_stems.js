const fs = require('fs');
const path = require('path');

function organizeStems(artist, title, sourceDir, stemsDir, overwrite = false) {
  if (!fs.existsSync(sourceDir)) {
    throw new Error(`Source directory not found: ${sourceDir}`);
  }
  
  if (!fs.existsSync(stemsDir)) {
    fs.mkdirSync(stemsDir, { recursive: true });
  }
  
  const expectedStems = ["Vocals", "Drums", "Bass", "Harmony", "Lead", "FX"];
  const stemsData = {
    track: title,
    artist: artist,
    export_date: new Date().toISOString(),
    stems: []
  };
  
  const files = fs.readdirSync(sourceDir);
  
  expectedStems.forEach(stemName => {
    const matchingFiles = files.filter(f => 
      f.toLowerCase().includes(stemName.toLowerCase()) && 
      (f.endsWith('.wav') || f.endsWith('.mp3'))
    );
    
    if (matchingFiles.length > 0) {
      if (matchingFiles.length > 1) {
        console.log(`⚠️  Multiple files match '${stemName}':`);
        matchingFiles.forEach(f => console.log(`     - ${f}`));
        console.log(`   Using: ${matchingFiles[0]}`);
      }
      
      const matchingFile = matchingFiles[0];
      const newName = `${artist} - ${title} - ${stemName}.wav`;
      const sourcePath = path.join(sourceDir, matchingFile);
      const destPath = path.join(stemsDir, newName);
      
      // Check for existing file
      if (fs.existsSync(destPath) && !overwrite) {
        throw new Error(
          `File already exists: ${destPath}\n` +
          `  To overwrite, set 'overwrite_existing: true' in config.json`
        );
      }
      
      fs.copyFileSync(sourcePath, destPath);
      
      stemsData.stems.push({
        name: stemName,
        file: newName,
        duration: "N/A"
      });
      
      console.log(`✓ Organized: ${newName}`);
    }
  });
  
  // Save metadata
  const metadataFile = path.join(stemsDir, `${artist} - ${title} - Stems_Metadata.json`);
  fs.writeFileSync(metadataFile, JSON.stringify(stemsData, null, 2));
  console.log(`✓ Generated metadata: ${metadataFile}`);
  
  return stemsData;
}

// Usage
if (require.main === module) {
  organizeStems('YourArtistName', 'Deep Dive', './exports/stems', './Releases/DeepDive/Stems');
}

module.exports = { organizeStems };

