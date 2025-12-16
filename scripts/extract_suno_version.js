const fs = require('fs');
const path = require('path');
const { URL } = require('url');

function extractSunoVersionFromUrl(trackUrl) {
  const parsed = new URL(trackUrl);
  
  // Extract track ID from path
  const pathMatch = parsed.pathname.match(/\/song\/([a-zA-Z0-9_-]+)/);
  const trackId = pathMatch ? pathMatch[1] : null;
  
  // Extract from query params
  const version = parsed.searchParams.get('v');
  const buildId = parsed.searchParams.get('build');
  
  return {
    track_id: trackId,
    version: version,
    build_id: buildId,
    url: trackUrl
  };
}

function extractFromMetadataFile(metadataPath) {
  if (!fs.existsSync(metadataPath)) {
    console.error(`✗ Metadata file not found: ${metadataPath}`);
    return null;
  }
  
  try {
    const data = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
    return {
      version: data.version || null,
      build_id: data.build_id || data.id || null,
      created_at: data.created_at || null,
      model_version: data.model_version || null
    };
  } catch (e) {
    console.error(`✗ Error reading metadata: ${e.message}`);
    return null;
  }
}

// Usage example
if (require.main === module) {
  const versionInfo = extractSunoVersionFromUrl('https://suno.com/song/abc123xyz?v=3.5.2');
  console.log(JSON.stringify(versionInfo, null, 2));
}

module.exports = { extractSunoVersionFromUrl, extractFromMetadataFile };

