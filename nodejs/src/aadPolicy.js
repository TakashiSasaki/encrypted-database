const cryptoUtils = require('./crypto');

class AadPolicyError extends Error {
    constructor(message) {
        super(message);
        this.name = 'AadPolicyError';
    }
}

class AadPolicy {
    constructor(name, envelopeType, buildContext) {
        this.name = name;
        this.envelopeType = envelopeType;
        this.buildContext = buildContext;
    }

    context(args) {
        return this.buildContext(args);
    }

    aadBytes(args) {
        // cryptoUtils.canonicalizeJson is the canonicalization boundary used by
        // the current prototype. It must be replaced or backed by an RFC 8785
        // JCS implementation before this format is considered interoperable.
        return cryptoUtils.canonicalizeJson(this.context(args));
    }
}

const RECORD_PAYLOAD_V1 = 'record-payload-v1';
const WRAP_DATABASE_KEY_V1 = 'wrap-database-key-v1';
const WRAP_RECORD_KEY_V1 = 'wrap-record-key-v1';

function recordPayloadV1Context({ objectUuid, schemaUuid, contentType, kid, alg }) {
    return {
        v: 1,
        aad_policy: RECORD_PAYLOAD_V1,
        object_uuid: objectUuid,
        schema_uuid: schemaUuid,
        content_type: contentType,
        kid: kid,
        alg: alg
    };
}

function wrapDatabaseKeyV1Context({ wrappedKid, wrappingKid }) {
    return {
        v: 1,
        aad_policy: WRAP_DATABASE_KEY_V1,
        wrapped_kid: wrappedKid,
        wrapping_kid: wrappingKid
    };
}

function wrapRecordKeyV1Context({ wrappedKid, wrappingKid }) {
    return {
        v: 1,
        aad_policy: WRAP_RECORD_KEY_V1,
        wrapped_kid: wrappedKid,
        wrapping_kid: wrappingKid
    };
}

const AAD_POLICY_REGISTRY = {
    [RECORD_PAYLOAD_V1]: new AadPolicy(RECORD_PAYLOAD_V1, 'aead', recordPayloadV1Context),
    [WRAP_DATABASE_KEY_V1]: new AadPolicy(WRAP_DATABASE_KEY_V1, 'key_wrap', wrapDatabaseKeyV1Context),
    [WRAP_RECORD_KEY_V1]: new AadPolicy(WRAP_RECORD_KEY_V1, 'key_wrap', wrapRecordKeyV1Context)
};

function getPolicy(policyName) {
    const policy = AAD_POLICY_REGISTRY[policyName];
    if (!policy) {
        throw new AadPolicyError(`Unknown AAD policy: ${policyName}`);
    }
    return policy;
}

function buildAadContext(policyName, args) {
    return getPolicy(policyName).context(args);
}

function buildAadBytes(policyName, args) {
    return getPolicy(policyName).aadBytes(args);
}

function selectPayloadPolicy({ envelopeV = 1, envelopeType = 'aead', alg = 'A256GCM' } = {}) {
    if (envelopeV === 1 && envelopeType === 'aead' && alg === 'A256GCM') {
        return RECORD_PAYLOAD_V1;
    }
    throw new AadPolicyError(
        `No registered payload AAD policy for envelopeV=${envelopeV}, envelopeType=${envelopeType}, alg=${alg}`
    );
}

function selectKeyWrapPolicy({ wrappedKeyClass, envelopeV = 1, envelopeType = 'key_wrap', alg = 'A256GCM' }) {
    if (envelopeV !== 1 || envelopeType !== 'key_wrap' || alg !== 'A256GCM') {
        throw new AadPolicyError(
            `No registered key-wrap AAD policy for envelopeV=${envelopeV}, envelopeType=${envelopeType}, alg=${alg}`
        );
    }

    if (wrappedKeyClass === 'database_kek') {
        return WRAP_DATABASE_KEY_V1;
    }
    if (wrappedKeyClass === 'record_dek' || wrappedKeyClass === 'file_dek') {
        return WRAP_RECORD_KEY_V1;
    }

    throw new AadPolicyError(`No registered key-wrap AAD policy for wrappedKeyClass=${wrappedKeyClass}`);
}

module.exports = {
    AadPolicyError,
    RECORD_PAYLOAD_V1,
    WRAP_DATABASE_KEY_V1,
    WRAP_RECORD_KEY_V1,
    AAD_POLICY_REGISTRY,
    getPolicy,
    buildAadContext,
    buildAadBytes,
    selectPayloadPolicy,
    selectKeyWrapPolicy
};
