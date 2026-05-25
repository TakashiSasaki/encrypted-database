package vault

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/hex"
	"path/filepath"
	"testing"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/vectors"
)

type KeyWrapVector struct {
	Name                                   string  `json:"name"`
	Description                            string  `json:"description"`
	AADPolicy                              string  `json:"aad_policy"`
	WrappedKeyClass                        string  `json:"wrapped_key_class"`
	WrappedKid                             string  `json:"wrapped_kid"`
	WrappingKid                            string  `json:"wrapping_kid"`
	WrappingKeyHex                         string  `json:"wrapping_key_hex"`
	WrappedKeyPlaintextHex                 string  `json:"wrapped_key_plaintext_hex"`
	NonceHex                               string  `json:"nonce_hex"`
	ExpectedAADHex                         string  `json:"expected_aad_hex"`
	ExpectedWrappedKeyCiphertextHex        string  `json:"expected_wrapped_key_ciphertext_hex"`
	ExpectedWrappedKeyTagHex               string  `json:"expected_wrapped_key_tag_hex"`
	ExpectedWrappedKeyCiphertextAndTagHex  string  `json:"expected_wrapped_key_ciphertext_and_tag_hex"`
	Valid                                  bool    `json:"valid"`
	Algorithm                              *string `json:"algorithm,omitempty"` // Assuming missing means A256GCM
}

func decodeHex(t *testing.T, s string) []byte {
	t.Helper()
	b, err := hex.DecodeString(s)
	if err != nil {
		t.Fatalf("Failed to decode hex %q: %v", s, err)
	}
	return b
}

func TestKeyWrapConformance(t *testing.T) {
	var v []KeyWrapVector
	err := vectors.LoadJSONVector(filepath.Join("key-wrap", "key-wrap-v1.json"), &v)
	if err != nil {
		t.Fatalf("Failed to load key-wrap test vectors: %v", err)
	}

	for _, tc := range v {
		t.Run(tc.Name, func(t *testing.T) {
			// Algorithm check
			alg := "A256GCM"
			if tc.Algorithm != nil {
				alg = *tc.Algorithm
			}
			if alg != "A256GCM" {
				if tc.Valid {
					t.Fatalf("Unsupported algorithm %q in positive test vector", alg)
				}
				// For explicit negative test with unsupported algorithm, we pass
				return
			}

			// Validate and decode lengths
			wrappingKey := decodeHex(t, tc.WrappingKeyHex)
			if len(wrappingKey) != 32 {
				t.Fatalf("Expected wrapping key length 32, got %d", len(wrappingKey))
			}

			plaintext := decodeHex(t, tc.WrappedKeyPlaintextHex)
			if len(plaintext) != 32 { // Assuming 32-byte key material
				t.Fatalf("Expected wrapped key plaintext length 32, got %d", len(plaintext))
			}

			nonce := decodeHex(t, tc.NonceHex)
			if len(nonce) != 12 {
				t.Fatalf("Expected nonce length 12, got %d", len(nonce))
			}

			var expectedCiphertextAndTag []byte
			if tc.ExpectedWrappedKeyCiphertextAndTagHex != "" {
			    expectedCiphertextAndTag = decodeHex(t, tc.ExpectedWrappedKeyCiphertextAndTagHex)
			}

			if tc.ExpectedWrappedKeyCiphertextHex != "" && tc.ExpectedWrappedKeyTagHex != "" {
			    expectedCiphertext := decodeHex(t, tc.ExpectedWrappedKeyCiphertextHex)
			    expectedTag := decodeHex(t, tc.ExpectedWrappedKeyTagHex)
			    if len(expectedTag) != 16 {
			        t.Fatalf("Expected tag length 16, got %d", len(expectedTag))
			    }
			    combined := append(expectedCiphertext, expectedTag...)
			    if expectedCiphertextAndTag != nil {
			        if hex.EncodeToString(combined) != hex.EncodeToString(expectedCiphertextAndTag) {
			            t.Fatalf("Separated ciphertext+tag do not match concatenated ciphertext_and_tag")
			        }
			    } else {
			        expectedCiphertextAndTag = combined
			    }
			}

			// AAD Reconstruction
			aadBytes, err := aad.BuildWrapKeyV1(tc.AADPolicy, tc.WrappedKid, tc.WrappingKid)
			if err != nil {
				if tc.Valid {
					t.Fatalf("AAD builder failed: %v", err)
				}
				return
			}

			aadHex := hex.EncodeToString(aadBytes)
			if tc.ExpectedAADHex != "" && aadHex != tc.ExpectedAADHex {
				t.Fatalf("Reconstructed AAD hex %q does not match expected %q", aadHex, tc.ExpectedAADHex)
			}

			// AES-GCM Encrypt
			block, err := aes.NewCipher(wrappingKey)
			if err != nil {
				t.Fatalf("Failed to create cipher: %v", err)
			}
			aesgcm, err := cipher.NewGCM(block)
			if err != nil {
				t.Fatalf("Failed to create GCM: %v", err)
			}

			// Go's cipher.AEAD.Seal appends the tag to the ciphertext, resulting in "ciphertext || tag"
			sealed := aesgcm.Seal(nil, nonce, plaintext, aadBytes)

			if tc.Valid {
			    if expectedCiphertextAndTag != nil && hex.EncodeToString(sealed) != hex.EncodeToString(expectedCiphertextAndTag) {
			        t.Errorf("Sealed output does not match expected.\nGot: %x\nExp: %x", sealed, expectedCiphertextAndTag)
			    }

			    // Decrypt
			    opened, err := aesgcm.Open(nil, nonce, expectedCiphertextAndTag, aadBytes)
			    if err != nil {
			        t.Errorf("Failed to open valid key-wrap: %v", err)
			    }
			    if hex.EncodeToString(opened) != hex.EncodeToString(plaintext) {
			        t.Errorf("Opened plaintext does not match expected.\nGot: %x\nExp: %x", opened, plaintext)
			    }
			} else {
			    // For negative test vectors, opening should fail
			    if expectedCiphertextAndTag != nil {
			        _, err := aesgcm.Open(nil, nonce, expectedCiphertextAndTag, aadBytes)
			        if err == nil {
			            t.Errorf("Expected failure to open negative key-wrap, but it succeeded")
			        }
			    }
			}
		})
	}
}
