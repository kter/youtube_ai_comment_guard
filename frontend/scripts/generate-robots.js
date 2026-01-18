#!/usr/bin/env node
/**
 * Generate robots.txt based on environment
 * - dev: Disallow all crawlers
 * - prd: Allow all crawlers
 */

import { writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = join(__dirname, '..', 'dist');
const robotsPath = join(distDir, 'robots.txt');

// Get environment from VITE_ENV or default to 'prd'
const env = process.env.VITE_ENV || 'prd';

const robotsContent = env === 'dev'
  ? `# Development environment - block all crawlers
User-agent: *
Disallow: /
`
  : `# Production environment - allow all crawlers
User-agent: *
Allow: /
`;

// Ensure dist directory exists
try {
  mkdirSync(distDir, { recursive: true });
} catch (e) {
  // Directory already exists
}

writeFileSync(robotsPath, robotsContent);
console.log(`Generated robots.txt for ${env} environment`);
