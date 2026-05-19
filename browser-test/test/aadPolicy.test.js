const { AadPolicyError, selectPayloadPolicy, selectKeyWrapPolicy, getPolicy, buildAadContext, buildAadBytes } = require('../src/aadPolicy');

describe('AadPolicy', () => {
    test('selectPayloadPolicy', () => {
        expect(selectPayloadPolicy()).toBe('record-payload-v1');
        expect(() => selectPayloadPolicy({ alg: 'unsupported' })).toThrow(AadPolicyError);
    });

    test('selectKeyWrapPolicy', () => {
        expect(selectKeyWrapPolicy({ wrappedKeyClass: 'database_kek' })).toBe('wrap-database-key-v1');
        expect(selectKeyWrapPolicy({ wrappedKeyClass: 'record_dek' })).toBe('wrap-record-key-v1');
        expect(() => selectKeyWrapPolicy({ wrappedKeyClass: 'unknown' })).toThrow(AadPolicyError);
        expect(() => selectKeyWrapPolicy({ wrappedKeyClass: 'record_dek', alg: 'unsupported' })).toThrow(AadPolicyError);
    });

    test('getPolicy throws on unknown policy', () => {
        expect(() => getPolicy('unknown-policy')).toThrow(AadPolicyError);
    });
});
