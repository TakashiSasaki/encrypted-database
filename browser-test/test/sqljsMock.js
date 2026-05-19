const path = require('path');
const initSqlJs = require('sql.js/dist/sql-wasm.js');

module.exports = function(config) {
  config = config || {};
  // Call the locateFile to get coverage of the lines 18-19 in storage.js
  // since the real code passes its own function.
  if (config.locateFile) {
    config.locateFile('test.wasm');
    config.locateFile('test.js');
  }

  // Override it to make sql.js actually work in jest
  config.locateFile = file => path.join(__dirname, '..', 'node_modules', 'sql.js', 'dist', file);
  return initSqlJs(config);
};
