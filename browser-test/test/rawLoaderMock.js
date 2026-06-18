const fs = require('fs');
const path = require('path');
// Since it's mapped from '/docs/backend/sqlite/schema.sql'
// The actual path will be relative to project root
const schemaPath = path.resolve(__dirname, '../../docs/backend/sqlite/schema.sql');
const content = fs.readFileSync(schemaPath, 'utf8');
module.exports = content;
