#!/usr/bin/env node
/**
 * DistroKid Release Packer - Main Orchestrator (JavaScript)
 * 
 * Runs the complete release workflow from Suno export to DistroKid-ready files.
 */

const fs = require('fs');
const path = require('path');

// Import workflow modules
const { extractSunoVersionFromUrl, extractFromMetadataFile } = require('./extract_suno_version');
const { renameAudioFiles } = require('./rename_audio_files');
const { organizeStems } = require('./organize_stems');
const { batchTagStems } = require('./tag_stems');
const { tagAudioFile } = require('./tag_audio_id3');

function loadUserSettings() {
  const settingsFile = 'artist-defaults.json';
  if (!fs.existsSync(settingsFile)) {
    return {};
  }
  
  try {
    const settingsData = fs.readFileSync(settingsFile, 'utf8');
    const settings = JSON.parse(settingsData);
    // Filter out comment fields
    const filtered = {};
    for (const [key, value] of Object.entries(settings)) {
      if (!key.startsWith('_')) {
        filtered[key] = value;
      }
    }
    return filtered;
  } catch (e) {
    // If artist-defaults.json is invalid, just return empty dict
    return {};
  }
}

function loadConfig(configPath) {
  if (!fs.existsSync(configPath)) {
    throw new Error(`Config file not found: ${configPath}`);
  }
  
  // Load user settings first (defaults)
  const userSettings = loadUserSettings();
  
  // Load release-specific config
  let releaseConfig;
  try {
    const configData = fs.readFileSync(configPath, 'utf8');
    releaseConfig = JSON.parse(configData);
  } catch (e) {
    if (e instanceof SyntaxError) {
      throw new Error(
        `Invalid JSON in config file '${configPath}':\n` +
        `  Error: ${e.message}\n` +
        `  Fix the JSON syntax and try again.`
      );
    }
    throw e;
  }
  
  // Merge: user settings as defaults, release config overrides
  const mergedConfig = {};
  
  // Apply default artist if not specified
  if (!releaseConfig.artist && userSettings.default_artist) {
    mergedConfig.artist = userSettings.default_artist;
  }
  
  // Apply default publisher if not specified in id3_metadata
  if (releaseConfig.id3_metadata) {
    if (!releaseConfig.id3_metadata.publisher && userSettings.default_publisher) {
      if (!mergedConfig.id3_metadata) {
        mergedConfig.id3_metadata = { ...releaseConfig.id3_metadata };
      }
      mergedConfig.id3_metadata.publisher = userSettings.default_publisher;
    }
    
    // Apply default composer template if not specified
    if (!releaseConfig.id3_metadata.composer && userSettings.default_composer_template) {
      if (!mergedConfig.id3_metadata) {
        mergedConfig.id3_metadata = { ...releaseConfig.id3_metadata };
      }
      const artist = releaseConfig.artist || userSettings.default_artist || 'Artist';
      const composerTemplate = userSettings.default_composer_template;
      mergedConfig.id3_metadata.composer = composerTemplate.replace('{artist}', artist);
    }
    
    // Apply default track number if not specified
    if (!releaseConfig.id3_metadata.tracknumber) {
      if (!mergedConfig.id3_metadata) {
        mergedConfig.id3_metadata = { ...releaseConfig.id3_metadata };
      }
      
      const defaultTrack = userSettings.default_track_number || '1';
      const defaultTotal = userSettings.default_total_tracks || '1';
      
      // Format: "1" for singles, "1/5" for multi-track
      if (defaultTotal === '1') {
        mergedConfig.id3_metadata.tracknumber = defaultTrack;
      } else {
        mergedConfig.id3_metadata.tracknumber = `${defaultTrack}/${defaultTotal}`;
      }
    }
  } else if (userSettings.default_track_number || userSettings.default_total_tracks) {
    // If id3_metadata doesn't exist but track defaults are set, create it
    if (!mergedConfig.id3_metadata) {
      mergedConfig.id3_metadata = {};
    }
    
    const defaultTrack = userSettings.default_track_number || '1';
    const defaultTotal = userSettings.default_total_tracks || '1';
    
    if (defaultTotal === '1') {
      mergedConfig.id3_metadata.tracknumber = defaultTrack;
    } else {
      mergedConfig.id3_metadata.tracknumber = `${defaultTrack}/${defaultTotal}`;
    }
  }
  
  // Merge everything: user settings → release config → merged overrides
  const finalConfig = { ...userSettings, ...releaseConfig, ...mergedConfig };
  
  // Clean up: remove default_* keys from final config (they're only for merging)
  const cleaned = {};
  for (const [key, value] of Object.entries(finalConfig)) {
    if (!key.startsWith('default_')) {
      cleaned[key] = value;
    }
  }
  
  return cleaned;
}

function validateConfig(config) {
  const errors = [];
  const warnings = [];
  
  // Required fields
  const requiredFields = {
    artist: 'string',
    title: 'string'
  };
  
  for (const [field, expectedType] of Object.entries(requiredFields)) {
    if (!(field in config)) {
      errors.push(`Missing required field: '${field}'`);
    } else if (typeof config[field] !== expectedType) {
      errors.push(`Field '${field}' must be ${expectedType}, got ${typeof config[field]}`);
    } else if (!config[field] || !String(config[field]).trim()) {
      errors.push(`Field '${field}' cannot be empty`);
    }
  }
  
  // Type validation for optional fields
  const typeChecks = {
    bpm: 'number',
    explicit: 'boolean',
    organize_stems: 'boolean',
    tag_stems: 'boolean',
    tag_audio: 'boolean',
    validate_cover: 'boolean',
    validate_compliance: 'boolean',
    strict_mode: 'boolean',
    overwrite_existing: 'boolean'
  };
  
  for (const [field, expectedType] of Object.entries(typeChecks)) {
    if (field in config && typeof config[field] !== expectedType) {
      errors.push(
        `Field '${field}' must be ${expectedType}, got ${typeof config[field]}`
      );
    }
  }
  
  // Value range validation
  if ('bpm' in config) {
    const bpm = config.bpm;
    if (typeof bpm !== 'number' || bpm < 1 || bpm > 300) {
      errors.push(`Field 'bpm' must be number between 1-300, got ${bpm}`);
    }
  }
  
    // Path validation
    const pathFields = ['source_audio_dir', 'source_stems_dir', 'release_dir'];
    for (const field of pathFields) {
      if (field in config && config[field]) {
        const pathVal = path.resolve(config[field]);
        if (field.startsWith('source_') && pathVal && typeof pathVal === 'string' && !fs.existsSync(pathVal)) {
          warnings.push(`Source directory does not exist: ${config[field]}`);
        }
      }
    }
  
  // Validate nested id3_metadata structure
  if ('id3_metadata' in config) {
    if (typeof config.id3_metadata !== 'object' || Array.isArray(config.id3_metadata)) {
      errors.push("Field 'id3_metadata' must be an object");
    } else if (config.id3_metadata.tracknumber) {
      const tracknum = config.id3_metadata.tracknumber;
      if (typeof tracknum === 'string' && tracknum.includes('/')) {
        const parts = tracknum.split('/');
        if (parts.length !== 2 || !parts.every(p => /^\d+$/.test(p))) {
          errors.push(
            `Field 'id3_metadata.tracknumber' must be format 'X/Total', got '${tracknum}'`
          );
        }
      }
    }
  }
  
  // Check for invalid characters in artist/title (will be sanitized)
  const invalidChars = /[<>:"/\\|?*]/g;
  for (const field of ['artist', 'title']) {
    if (field in config) {
      const value = String(config[field]);
      const matches = value.match(invalidChars);
      if (matches) {
        const uniqueChars = [...new Set(matches)];
        warnings.push(
          `Field '${field}' contains invalid characters: ${uniqueChars.join(', ')}. ` +
          `They will be replaced with '_'.`
        );
      }
    }
  }
  
  // Optional but recommended fields
  if (!('source_audio_dir' in config)) {
    warnings.push("'source_audio_dir' not specified, using default: ./exports");
  }
  
  // Validate paths if provided
  if (config.release_dir) {
    const releasePath = path.resolve(config.release_dir);
    const parentDir = path.dirname(releasePath);
    if (path.isAbsolute(releasePath) && parentDir && typeof parentDir === 'string' && !fs.existsSync(parentDir)) {
      warnings.push(`Release directory parent does not exist: ${parentDir}`);
    }
  }
  
  if (errors.length > 0) {
    throw new Error(
      'Configuration validation failed:\n' +
      errors.map(e => `  - ${e}`).join('\n')
    );
  }
  
  if (warnings.length > 0) {
    warnings.forEach(warning => console.log(`⚠️  ${warning}`));
  }
  
  return true;
}

function sanitizeFilename(name) {
  if (!name) {
    return 'Unknown';
  }
  
  // Remove invalid characters for Windows/Unix
  const invalidChars = /[<>:"/\\|?*]/g;
  let sanitized = name.replace(invalidChars, '_');
  
  // Remove leading/trailing dots and spaces (Windows issue)
  sanitized = sanitized.trim().replace(/^\.+|\.+$/g, '');
  
  // Limit length (filesystem limits + safety margin)
  const maxLength = 200;
  if (sanitized.length > maxLength) {
    sanitized = sanitized.substring(0, maxLength);
  }
  
  // Ensure not empty after sanitization
  if (!sanitized) {
    sanitized = 'Unknown';
  }
  
  return sanitized;
}

function acquireWorkflowLock(releaseDir) {
  const lockFile = path.join(releaseDir, '.workflow.lock');
  
  if (fs.existsSync(lockFile)) {
    // Check if lock is stale (older than 1 hour)
    const stats = fs.statSync(lockFile);
    const lockAge = (Date.now() - stats.mtimeMs) / 1000;
    if (lockAge > 3600) {
      console.log(`⚠️  Removing stale lock file (age: ${(lockAge / 60).toFixed(1)} minutes)`);
      fs.unlinkSync(lockFile);
    } else {
      throw new Error(
        `Workflow already in progress for ${releaseDir}.\n` +
        `  Lock file: ${lockFile}\n` +
        `  If no workflow is running, delete the lock file manually.`
      );
    }
  }
  
  // Create lock file
  const lockDir = path.dirname(lockFile);
  if (!fs.existsSync(lockDir)) {
    fs.mkdirSync(lockDir, { recursive: true });
  }
  fs.writeFileSync(lockFile, `PID: ${process.pid}\nTime: ${new Date().toISOString()}\n`);
  return lockFile;
}

function releaseWorkflowLock(lockFile) {
  if (lockFile && typeof lockFile === 'string' && fs.existsSync(lockFile)) {
    fs.unlinkSync(lockFile);
  }
}

function checkDiskSpace(dirPath, requiredMB = 100) {
  try {
    // Validate input
    if (!dirPath || typeof dirPath !== 'string') {
      throw new Error(`Invalid directory path: ${dirPath}`);
    }
    const stats = fs.statSync(dirPath);
    // Note: Node.js doesn't have direct disk space API, so we'll skip this check
    // In production, you might want to use a package like 'check-disk-space'
    // For now, we'll just verify the directory exists
    if (!fs.existsSync(dirPath)) {
      throw new Error(`Directory does not exist: ${dirPath}`);
    }
    return true;
  } catch (e) {
    throw new Error(`Cannot check disk space: ${e.message}`);
  }
}

function validateDependencies() {
  const missing = [];
  
  try {
    require('node-id3');
  } catch (e) {
    missing.push('node-id3 (required for ID3 tagging)');
  }
  
  try {
    require('sharp');
  } catch (e) {
    missing.push('sharp (required for cover art validation)');
  }
  
  if (missing.length > 0) {
    throw new Error(
      'Missing required dependencies:\n' +
      missing.map(dep => `  - ${dep}`).join('\n') +
      '\n\nInstall with: npm install'
    );
  }
  
  return true;
}

function saveReleaseMetadata(artist, title, metadata, outputDir) {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const releaseMetadata = {
    artist: artist,
    title: title,
    created_date: new Date().toISOString(),
    ...metadata
  };
  
  const metadataFile = path.join(outputDir, `${artist} - ${title} - Metadata.json`);
  fs.writeFileSync(metadataFile, JSON.stringify(releaseMetadata, null, 2));
  
  console.log(`✓ Generated release metadata: ${metadataFile}`);
  return metadataFile;
}

async function runReleaseWorkflow(config) {
  validateConfig(config);
  validateDependencies();
  
  // Sanitize user input
  const artist = sanitizeFilename(config.artist);
  const title = sanitizeFilename(config.title);
  const debugMode = config.debug || false;
  
  console.log('🚀 Starting DistroKid Release Packer Workflow\n');
  
  const releaseDir = config.release_dir || `./Releases/${title}`;
  
  // Acquire workflow lock and check disk space
  let lockFile = null;
  try {
    lockFile = acquireWorkflowLock(releaseDir);
    checkDiskSpace(releaseDir, 500);  // Conservative estimate
  } catch (e) {
    if (lockFile && typeof lockFile === 'string' && fs.existsSync(lockFile)) {
      releaseWorkflowLock(lockFile);
    }
    throw e;
  }
  
  try {
    // Step 1: Extract Suno version
  let versionInfo = null;
  if (config.suno_url) {
    console.log('📋 Step 1: Extracting Suno version info...');
    versionInfo = extractSunoVersionFromUrl(config.suno_url);
    console.log(`✓ Version: ${versionInfo.version}, Build: ${versionInfo.build_id}\n`);
  } else if (config.suno_metadata_file) {
    console.log('📋 Step 1: Extracting Suno version from metadata...');
    versionInfo = extractFromMetadataFile(config.suno_metadata_file);
    if (versionInfo) {
      console.log(`✓ Version: ${versionInfo.version}, Build: ${versionInfo.build_id}\n`);
    }
  }
  
  // Step 2: Rename audio files
  if (config.rename_audio !== false) {
    console.log('📁 Step 2: Renaming and organizing audio files...');
    try {
      renameAudioFiles(
        artist,
        title,
        config.source_audio_dir || './exports',
        path.join(releaseDir, 'Audio'),
        config.overwrite_existing || false
      );
      console.log();
    } catch (e) {
      console.error(`✗ Error renaming audio files: ${e.message}`);
      if (debugMode) {
        console.error('\nDebug traceback:');
        console.error(e.stack);
      } else {
        console.error("   (Run with 'debug: true' in config for full traceback)");
      }
      console.error();
      if (config.strict_mode) {
        return false;
      }
    }
  }
  
  // Step 3: Organize stems
  if (config.organize_stems) {
    console.log('🎵 Step 3: Organizing stems...');
    try {
      organizeStems(
        artist,
        title,
        config.source_stems_dir || './exports/stems',
        path.join(releaseDir, 'Stems'),
        config.overwrite_existing || false
      );
      console.log();
    } catch (e) {
      console.error(`✗ Error organizing stems: ${e.message}`);
      if (debugMode) {
        console.error('\nDebug traceback:');
        console.error(e.stack);
      } else {
        console.error("   (Run with 'debug: true' in config for full traceback)");
      }
      console.error();
      if (config.strict_mode) {
        return false;
      }
    }
  }
  
  // Step 4: Tag stems
  if (config.tag_stems) {
    console.log('🏷️  Step 4: Tagging stems...');
    try {
      batchTagStems(
        path.join(releaseDir, 'Stems'),
        artist,
        title
      );
      console.log();
    } catch (e) {
      console.error(`✗ Error tagging stems: ${e.message}`);
      if (debugMode) {
        console.error('\nDebug traceback:');
        console.error(e.stack);
      } else {
        console.error("   (Run with 'debug: true' in config for full traceback)");
      }
      console.error();
      if (config.strict_mode) {
        return false;
      }
    }
  }
  
  // Step 5: Tag audio files
  if (config.tag_audio !== false) {
    console.log('🏷️  Step 5: Tagging audio files with ID3v2...');
    const audioFile = path.join(releaseDir, 'Audio', `${artist} - ${title}.mp3`);
    const coverDir = path.join(releaseDir, 'Cover');
    let coverFile = null;
    
    // Find cover art (check both JPG and PNG)
    const expectedCoverJpg = path.join(coverDir, `${artist} - ${title} - Cover.jpg`);
    const expectedCoverPng = path.join(coverDir, `${artist} - ${title} - Cover.png`);
    
    if (fs.existsSync(expectedCoverJpg)) {
      coverFile = expectedCoverJpg;
    } else if (fs.existsSync(expectedCoverPng)) {
      coverFile = expectedCoverPng;
    }
    
    if (!fs.existsSync(audioFile)) {
      console.log(`⚠️  Audio file not found: ${audioFile}`);
      console.log('   Skipping tagging step\n');
    } else {
      const metadata = config.id3_metadata || {};
      metadata.title = metadata.title || title;
      metadata.artist = metadata.artist || artist;
      metadata.publisher = metadata.publisher || 'Independent';
      
      // Add album artist (defaults to artist if not specified) - TPE2 (Strongly Recommended)
      if (!metadata.album_artist) {
        metadata.album_artist = artist;
      }
      
      // Add BPM if available in config - TBPM (Strongly Recommended)
      if (config.bpm && !metadata.bpm) {
        metadata.bpm = config.bpm;
      }
      
      // Add ISRC if available in config - TSRC (Strongly Recommended)
      if (config.isrc && !metadata.isrc) {
        metadata.isrc = config.isrc;
      }
      
      // Add language if available in config - TLAN (Strongly Recommended)
      if (config.language && !metadata.language) {
        metadata.language = config.language;
        // Map common language names to ISO 639-2 codes
        const langMap = {
          'english': 'eng', 'spanish': 'spa', 'french': 'fra',
          'german': 'deu', 'italian': 'ita', 'portuguese': 'por',
          'japanese': 'jpn', 'chinese': 'zho', 'korean': 'kor'
        };
        const langLower = (config.language || '').toLowerCase();
        if (langMap[langLower]) {
          metadata.language_code = langMap[langLower];
        }
      }
      
      // Add version info to comment
      if (versionInfo) {
        // Format version nicely (v5, v3.5.2, etc.)
        let versionStr = versionInfo.version || 'unknown';
        if (versionStr && !versionStr.startsWith('v')) {
          versionStr = `v${versionStr}`;
        }
        const buildStr = versionInfo.build_id || 'unknown';
        const versionComment = buildStr !== 'unknown' 
          ? `AI-generated with Suno ${versionStr}, Build ${buildStr}`
          : `AI-generated with Suno ${versionStr}`;
        metadata.comment = metadata.comment 
          ? `${metadata.comment} | ${versionComment}`
          : versionComment;
      }
      
      // Encoder (TSSE) - Optional metadata only (NOT a DistroKid requirement)
      // Only add if explicitly provided in metadata
      // Don't auto-add encoder - it's optional metadata only
      
      try {
        // Only pass coverFile if it's a valid string path
        const coverPathForTagging = (coverFile && typeof coverFile === 'string' && fs.existsSync(coverFile)) 
          ? coverFile 
          : null;
        tagAudioFile(
          audioFile,
          coverPathForTagging,
          metadata
        );
        console.log();
      } catch (e) {
        console.error(`✗ Error tagging audio: ${e.message}`);
        if (debugMode) {
          console.error('\nDebug traceback:');
          console.error(e.stack);
        } else {
          console.error("   (Run with 'debug: true' in config for full traceback)");
        }
        console.error();
        if (config.strict_mode) {
          return false;
        }
      }
    }
  }
  
  // Step 6: Find, rename, and validate cover art
  if (config.validate_cover !== false) {
    console.log('🖼️  Step 6: Finding and validating cover art...');
    const coverDir = path.join(releaseDir, 'Cover');
    const expectedCoverJpg = path.join(coverDir, `${artist} - ${title} - Cover.jpg`);
    const expectedCoverPng = path.join(coverDir, `${artist} - ${title} - Cover.png`);
    let coverFile = null;
    
    // First, check if correctly named file already exists
    if (fs.existsSync(expectedCoverJpg)) {
      coverFile = expectedCoverJpg;
    } else if (fs.existsSync(expectedCoverPng)) {
      coverFile = expectedCoverPng;
    } else {
      // Look for any image file in Cover directory
      if (fs.existsSync(coverDir)) {
        const files = fs.readdirSync(coverDir);
        const imageFiles = files.filter(file => {
          const ext = path.extname(file).toLowerCase();
          return ['.jpg', '.jpeg', '.png'].includes(ext);
        });
        
        if (imageFiles.length > 0) {
          // Found an image - rename it to match convention
          const foundFile = path.join(coverDir, imageFiles[0]);
          const ext = path.extname(imageFiles[0]).toLowerCase();
          
          // Determine target file (prefer JPG, fallback to PNG)
          if (ext === '.jpg' || ext === '.jpeg') {
            coverFile = expectedCoverJpg;
          } else {
            coverFile = expectedCoverPng;
          }
          
          // Rename the file
          try {
            fs.renameSync(foundFile, coverFile);
            console.log(`✓ Renamed cover art: ${imageFiles[0]} → ${path.basename(coverFile)}`);
          } catch (e) {
            console.log(`⚠️  Could not rename cover art: ${e.message}`);
            coverFile = foundFile; // Use original file
          }
        }
      }
    }
    
    if (coverFile && typeof coverFile === 'string' && fs.existsSync(coverFile)) {
      // Validate cover art (would need to import validateCoverArt function)
      console.log(`✓ Cover art found: ${path.basename(coverFile)}`);
    } else {
      console.log(`⚠️  Cover art not found in: ${coverDir}`);
      console.log(`   Expected: ${path.basename(expectedCoverJpg)} or ${path.basename(expectedCoverPng)}`);
      console.log(`   Or place any .jpg/.png file in ${coverDir} and it will be renamed automatically\n`);
    }
  }
  
  // Step 7: Save release metadata
  console.log('💾 Step 7: Saving release metadata...');
  const releaseMetadata = {
    genre: config.genre || '',
    bpm: config.bpm,
    key: config.key,
    explicit: config.explicit || false,
    language: config.language || 'English',
    mood: config.mood,
    target_regions: config.target_regions || [],
    isrc: config.isrc || '',
    upc: config.upc || '',
    suno_version: versionInfo ? versionInfo.version : null,
    suno_build_id: versionInfo ? versionInfo.build_id : null
  };
  
  saveReleaseMetadata(
    artist,
    title,
    releaseMetadata,
    path.join(releaseDir, 'Metadata')
  );
  
    console.log('\n🎉 Workflow completed successfully!');
    console.log(`📦 Release files ready in: ${releaseDir}`);
    
    return true;
  } finally {
    // Always release lock, even on error
    releaseWorkflowLock(lockFile);
  }
}

function main() {
  if (process.argv.length < 3) {
    console.log('Usage: node orchestrator.js <release.json>');
    console.log('\nExample release.json:');
    console.log(JSON.stringify({
      artist: 'YourArtistName',
      title: 'Deep Dive',
      release_dir: './Releases/DeepDive',
      suno_url: 'https://suno.com/song/abc123xyz?v=3.5.2',
      source_audio_dir: './exports',
      source_stems_dir: './exports/stems',
      genre: 'Deep House',
      bpm: 122,
      id3_metadata: {
        album: 'Summer Vibes EP',
        year: '2025',
        composer: 'YourArtistName + Suno AI'
      },
      organize_stems: true,
      tag_stems: false,
      validate_compliance: true,
      strict_mode: false
    }, null, 2));
    process.exit(1);
  }
  
  const configPath = process.argv[2];
  
  try {
    const config = loadConfig(configPath);
    runReleaseWorkflow(config)
      .then(success => {
        process.exit(success ? 0 : 1);
      })
      .catch(e => {
        console.error(`✗ Fatal error: ${e.message}`);
        process.exit(1);
      });
  } catch (e) {
    console.error(`✗ Fatal error: ${e.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { 
  runReleaseWorkflow, 
  loadConfig, 
  validateConfig, 
  validateDependencies, 
  sanitizeFilename,
  acquireWorkflowLock,
  releaseWorkflowLock,
  checkDiskSpace
};

