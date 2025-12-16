#!/usr/bin/env node
/**
 * DistroKid Release Packer - Main CLI Entry Point (JavaScript)
 * 
 * Simple command-line interface for the release packer.
 * Usage: node pack.js [command] [options]
 */

const fs = require('fs');
const path = require('path');
const { runReleaseWorkflow, loadConfig } = require('./scripts/orchestrator');

function showHelp() {
  console.log(`
DistroKid Release Packer - CLI Tool

USAGE:
  node pack.js <release.json>           Run complete workflow
  node pack.js --help                   Show this help
  node pack.js --example                Show example config

COMMANDS:
  pack <release.json>                    Process release with config file
  
EXAMPLES:
  node pack.js release.json
  node pack.js my-release.json

QUICK START:
  1. Copy release.example.json to release.json
  2. Edit release.json with your track details
  3. Run: node pack.js release.json

For more info, see:
  - docs/QUICK_START.md
  - scripts/README.md
  - docs/HOW_IT_WORKS.md
`);
}

function showExampleConfig() {
  const example = {
    artist: 'Your Artist Name',
    title: 'Your Track Title',
    release_dir: './Releases/YourTrack',
    suno_url: 'https://suno.com/song/your-track-id?v=3.5.2',
    source_audio_dir: './exports',
    source_stems_dir: './exports/stems',
    genre: 'Deep House',
    bpm: 122,
    id3_metadata: {
      album: 'Your Album Name',
      year: '2025',
      composer: 'Your Name + Suno AI',
      publisher: 'Independent'
    },
    organize_stems: true,
    tag_stems: false,
    tag_audio: true,
    validate_compliance: true,
    strict_mode: false
  };
  
  console.log('\nExample release.json:');
  console.log(JSON.stringify(example, null, 2));
  console.log('\nSave this as \'release.json\' and edit with your details.');
}

function main() {
  if (process.argv.length < 3) {
    showHelp();
    process.exit(1);
  }
  
  const command = process.argv[2];
  
  if (command === '--help' || command === '-h' || command === 'help') {
    showHelp();
    process.exit(0);
  }
  
  if (command === '--example' || command === '-e' || command === 'example') {
    showExampleConfig();
    process.exit(0);
  }
  
  // Assume it's a config file path
  const configPath = command;
  
  if (!fs.existsSync(configPath)) {
    console.error(`✗ Config file not found: ${configPath}`);
    console.log('\nCreate a config file first:');
    console.log('  1. Copy release.example.json to release.json');
    console.log('  2. Edit release.json with your track details');
    console.log('  3. Run: node pack.js release.json');
    process.exit(1);
  }
  
  try {
    console.log(`📋 Loading config: ${configPath}\n`);
    const config = loadConfig(configPath);
    
    runReleaseWorkflow(config)
      .then(success => {
        if (success) {
          console.log('\n✅ Success! Your release is ready for DistroKid upload.');
          process.exit(0);
        } else {
          console.log('\n⚠️  Workflow completed with warnings. Review output above.');
          process.exit(1);
        }
      })
      .catch(e => {
        console.error(`\n✗ Error: ${e.message}`);
        console.log('\nTroubleshooting:');
        console.log('  - Check that release.json is valid JSON');
        console.log('  - Verify all file paths exist');
        console.log('  - See docs/QUICK_START.md for help');
        process.exit(1);
      });
  } catch (e) {
    console.error(`\n✗ Error: ${e.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { main };

