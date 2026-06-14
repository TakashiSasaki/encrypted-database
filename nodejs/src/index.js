const EncryptedStorage = require('./storage');
const errors = require('./errors');

module.exports = {
    EncryptedStorage,
    errors,
    ...errors // Spread errors so they can be destructured directly if desired, similar to Python's approach
};
