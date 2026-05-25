package aad

import (
	"fmt"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
)

func BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, kid, alg string) ([]byte, error) {
	if objectUUID == "" || schemaUUID == "" || contentType == "" || kid == "" || alg == "" {
		return nil, fmt.Errorf("missing required fields for policy record-payload-v1")
	}
	contextMap := map[string]interface{}{
		"v":            1,
		"aad_policy":   "record-payload-v1",
		"object_uuid":  objectUUID,
		"schema_uuid":  schemaUUID,
		"content_type": contentType,
		"kid":          kid,
		"alg":          alg,
	}
	str, err := jcs.Canonicalize(contextMap)
	if err != nil {
		return nil, err
	}
	return []byte(str), nil
}

func BuildWrapKeyV1(policy, wrappedKid, wrappingKid string) ([]byte, error) {
	if policy != "wrap-database-key-v1" && policy != "wrap-record-key-v1" {
		return nil, fmt.Errorf("unsupported key wrap policy: %s", policy)
	}
	if wrappedKid == "" || wrappingKid == "" {
		return nil, fmt.Errorf("missing required fields for policy %s", policy)
	}
	contextMap := map[string]interface{}{
		"v":            1,
		"aad_policy":   policy,
		"wrapped_kid":  wrappedKid,
		"wrapping_kid": wrappingKid,
	}
	str, err := jcs.Canonicalize(contextMap)
	if err != nil {
		return nil, err
	}
	return []byte(str), nil
}
