package vault_test

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/hex"
	"testing"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/vectors"
)

func TestPayloadConformance(t *testing.T) {
	var vecs []map[string]interface{}
	err := vectors.LoadJSONVector("payload/payload-encryption-v1.json", &vecs)
	if err != nil {
		t.Fatalf("failed to load vectors: %v", err)
	}

	for _, vec := range vecs {
		t.Run(vec["name"].(string), func(t *testing.T) {
			valid, ok := vec["valid"].(bool)
			if !ok {
				t.Fatalf("missing or invalid 'valid' field")
			}

			// Validate algorithm
			algVal, ok := vec["alg"]
			if !ok || algVal == nil {
				if valid {
					t.Fatalf("missing alg")
				}
				return
			}
			alg := algVal.(string)
			if alg != "A256GCM" {
				if valid {
					t.Fatalf("unsupported algorithm: %s in positive test", alg)
				} else {
					t.Skipf("unsupported alg %s in negative test, explicit failure assumed", alg)
				}
			}

			// Decode key and nonce
			keyHexVal, ok := vec["record_dek_hex"]
			if !ok || keyHexVal == nil {
				if valid {
					t.Fatalf("missing record_dek_hex")
				}
				return
			}
			keyHex := keyHexVal.(string)
			key, err := hex.DecodeString(keyHex)
			if err != nil {
				if valid {
					t.Fatalf("invalid key hex: %v", err)
				}
				return
			}
			if len(key) != 32 {
				if valid {
					t.Fatalf("invalid key length: %d", len(key))
				}
				return
			}

			nonceHexVal, ok := vec["nonce_hex"]
			if !ok || nonceHexVal == nil {
				if valid {
					t.Fatalf("missing nonce_hex")
				}
				return
			}
			nonceHex := nonceHexVal.(string)
			nonce, err := hex.DecodeString(nonceHex)
			if err != nil {
				if valid {
					t.Fatalf("invalid nonce hex: %v", err)
				}
				return
			}
			if len(nonce) != 12 {
				if valid {
					t.Fatalf("invalid nonce length: %d", len(nonce))
				}
				return
			}

			// Check expected_tag_hex
			expectedTagHexVal, ok := vec["expected_tag_hex"]
			if ok && expectedTagHexVal != nil {
				tag, err := hex.DecodeString(expectedTagHexVal.(string))
				if err != nil {
					if valid {
						t.Fatalf("invalid expected_tag_hex: %v", err)
					}
					return
				}
				if len(tag) != 16 {
					if valid {
						t.Fatalf("invalid tag length: %d", len(tag))
					}
					return
				}
			}

			// Construct AAD
			objectUUIDVal, ok1 := vec["object_uuid"]
			schemaUUIDVal, ok2 := vec["schema_uuid"]
			contentTypeVal, ok3 := vec["content_type"]
			kidVal, ok4 := vec["kid"]

			if !ok1 || objectUUIDVal == nil || !ok2 || schemaUUIDVal == nil || !ok3 || contentTypeVal == nil || !ok4 || kidVal == nil {
				if valid {
					t.Fatalf("missing AAD reconstruction fields")
				}
				return
			}

			objectUUID := objectUUIDVal.(string)
			schemaUUID := schemaUUIDVal.(string)
			contentType := contentTypeVal.(string)
			kid := kidVal.(string)

			reconstructedAad, err := aad.BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, kid, alg)
			if err != nil {
				t.Fatalf("failed to reconstruct AAD: %v", err)
			}

			expectedAadHexVal, ok := vec["expected_aad_hex"]
			if ok && expectedAadHexVal != nil {
				expectedAad, err := hex.DecodeString(expectedAadHexVal.(string))
				if err != nil {
					t.Fatalf("invalid expected_aad_hex: %v", err)
				}
				if valid {
					if string(expectedAad) != string(reconstructedAad) {
						t.Fatalf("reconstructed AAD does not match expected_aad_hex\nExpected: %x\nGot:      %x", expectedAad, reconstructedAad)
					}
				}
			}

			// Process payload_json
			payloadJSON, ok := vec["payload_json"]
			if !ok || payloadJSON == nil {
				if valid {
					t.Fatalf("missing payload_json")
				}
				return
			}
			canonicalPayloadStr, err := jcs.Canonicalize(payloadJSON)
			if err != nil {
				if valid {
					t.Fatalf("failed to canonicalize payload_json: %v", err)
				}
				return
			}
			canonicalPayload := []byte(canonicalPayloadStr)

			expectedPayloadJcsHexVal, ok := vec["expected_payload_jcs_hex"]
			if ok && expectedPayloadJcsHexVal != nil {
				expectedPayloadJcs, err := hex.DecodeString(expectedPayloadJcsHexVal.(string))
				if err != nil {
					if valid {
						t.Fatalf("invalid expected_payload_jcs_hex: %v", err)
					}
					return
				}
				if string(expectedPayloadJcs) != string(canonicalPayload) {
					if valid {
						t.Fatalf("canonical payload does not match expected_payload_jcs_hex\nExpected: %x\nGot:      %x", expectedPayloadJcs, canonicalPayload)
					}
				}
			}

			// Prepare GCM
			block, err := aes.NewCipher(key)
			if err != nil {
				t.Fatalf("failed to create cipher: %v", err)
			}
			aesgcm, err := cipher.NewGCM(block)
			if err != nil {
				t.Fatalf("failed to create GCM: %v", err)
			}

			// We need expected_ciphertext_and_tag_hex
			expectedCiphertextAndTagHexVal, ok := vec["expected_ciphertext_and_tag_hex"]
			var expectedCiphertextAndTag []byte
			if ok && expectedCiphertextAndTagHexVal != nil {
				expectedCiphertextAndTag, err = hex.DecodeString(expectedCiphertextAndTagHexVal.(string))
				if err != nil {
					if valid {
						t.Fatalf("invalid expected_ciphertext_and_tag_hex: %v", err)
					}
					return
				}
			}

			// If it's a valid vector, encrypting our canonical payload with reconstructed AAD MUST match exactly.
			if valid {
				encrypted := aesgcm.Seal(nil, nonce, canonicalPayload, reconstructedAad)
				if ok && expectedCiphertextAndTagHexVal != nil && string(expectedCiphertextAndTag) != string(encrypted) {
					t.Fatalf("encrypted payload does not match expected_ciphertext_and_tag_hex\nExpected: %x\nGot:      %x", expectedCiphertextAndTag, encrypted)
				}

				// Perform decryption
				decrypted, err := aesgcm.Open(nil, nonce, expectedCiphertextAndTag, reconstructedAad)
				if err != nil {
					t.Fatalf("decryption failed on valid vector: %v", err)
				}
				if string(decrypted) != string(canonicalPayload) {
					t.Fatalf("decrypted payload does not match original canonical payload")
				}
			} else {
				// For invalid vectors, we are mostly testing DECRYPTION failures (e.g. AAD mismatch).
				if ok && expectedCiphertextAndTagHexVal != nil {
					_, err := aesgcm.Open(nil, nonce, expectedCiphertextAndTag, reconstructedAad)
					if err == nil {
						t.Fatalf("decryption succeeded on invalid vector, expected failure")
					}
				}
			}
		})
	}
}
