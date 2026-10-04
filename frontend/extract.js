const fs = require('fs');
const content = fs.readFileSync('src/app/simulator/investigate/page.tsx', 'utf8');
const lines = content.split('\n');

for(let i=0; i<lines.length; i++) {
  if (lines[i].match(/^(export\s+)?(function|const)\s+([A-Z]\w*)/) || lines[i].match(/export default function/)) {
    console.log(`Line ${i+1}: ${lines[i]}`);
  }
}
