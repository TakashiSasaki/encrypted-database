package aad

import (
	"encoding/hex"
	"path/filepath"
	"testing"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/vectors"
)

type AADVectorInput struct {
	ObjectUUID  *string `json:"object_uuid,omitempty"`
	SchemaUUID  *string `json:"schema_uuid,omitempty"`
	ContentType *string `json:"content_type,omitempty"`
	Kid         *string `json:"kid,omitempty"`
	Alg         *string `json:"alg,omitempty"`
	WrappedKid  *string `json:"wrapped_kid,omitempty"`
	WrappingKid *string `json:"wrapping_kid,omitempty"`
}

type AADVector struct {
	Name           string         `json:"name"`
	Policy         string         `json:"policy"`
	Description    string         `json:"description"`
	ExpectedHex    string         `json:"expected_hex"`
	ExpectedString *string        `json:"expected_string,omitempty"`
	Input          AADVectorInput `json:"input"`
}

func TestAADConformance(t *testing.T) {
	var v []AADVector
	err := vectors.LoadJSONVector(filepath.Join("aad", "aad-policies-v1.json"), &v)
	if err != nil {
		t.Fatalf("Failed to load AAD test vectors: %v", err)
	}

	for _, tc := range v {
		t.Run(tc.Name, func(t *testing.T) {
			var canonicalBytes []byte
			var err error

			switch tc.Policy {
			case "record-payload-v1":
				if tc.Input.ObjectUUID == nil || tc.Input.SchemaUUID == nil || tc.Input.ContentType == nil || tc.Input.Kid == nil || tc.Input.Alg == nil {
					t.Fatalf("Missing required fields for policy record-payload-v1")
				}
				canonicalBytes, err = BuildRecordPayloadV1(*tc.Input.ObjectUUID, *tc.Input.SchemaUUID, *tc.Input.ContentType, *tc.Input.Kid, *tc.Input.Alg)
			case "wrap-database-key-v1", "wrap-record-key-v1":
				if tc.Input.WrappedKid == nil || tc.Input.WrappingKid == nil {
					t.Fatalf("Missing required fields for policy %s", tc.Policy)
				}
				canonicalBytes, err = BuildWrapKeyV1(tc.Policy, *tc.Input.WrappedKid, *tc.Input.WrappingKid)
			default:
				t.Fatalf("Unknown or unsupported policy: %s", tc.Policy)
			}

			if err != nil {
				t.Fatalf("AAD builder failed: %v", err)
			}
			canonicalString := string(canonicalBytes)

			if tc.ExpectedString != nil && canonicalString != *tc.ExpectedString {
				t.Errorf("Expected string %q, got %q", *tc.ExpectedString, canonicalString)
			}

			canonicalHex := hex.EncodeToString(canonicalBytes)
			if canonicalHex != tc.ExpectedHex {
				t.Errorf("Expected hex %q, got %q", tc.ExpectedHex, canonicalHex)
			}
		})
	}
}
