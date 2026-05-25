package vault

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/hex"
	"path/filepath"
	"testing"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/vectors"
)

type AEADVector struct {
	Name                        string `json:"name"`
	Description                 string `json:"description"`
	Alg                         string `json:"alg"`
	KeyHex                      string `json:"key_hex"`
	NonceHex                    string `json:"nonce_hex"`
	AadHex                      string `json:"aad_hex"`
	PlaintextHex                string `json:"plaintext_hex"`
	ExpectedCiphertextHex       string `json:"expected_ciphertext_hex"`
	ExpectedTagHex              string `json:"expected_tag_hex"`
	ExpectedCiphertextAndTagHex string `json:"expected_ciphertext_and_tag_hex"`
	Valid                       bool   `json:"valid"`
}

func TestAEADConformance(t *testing.T) {
	var v []AEADVector
	err := vectors.LoadJSONVector(filepath.Join("aead", "aes-256-gcm-v1.json"), &v)
	if err != nil {
		t.Fatalf("Failed to load AEAD test vectors: %v", err)
	}

	for _, tc := range v {
		t.Run(tc.Name, func(t *testing.T) {
			if tc.Alg != "A256GCM" {
				if tc.Valid {
					t.Fatalf("Unsupported algorithm in valid vector: %s", tc.Alg)
				} else {
					// Expected failure for unsupported algorithm
					return
				}
			}

			key, err := hex.DecodeString(tc.KeyHex)
			if err != nil {
				t.Fatalf("Invalid key_hex: %v", err)
			}
			if len(key) != 32 {
				t.Fatalf("Expected key length 32, got %d", len(key))
			}

			nonce, err := hex.DecodeString(tc.NonceHex)
			if err != nil {
				t.Fatalf("Invalid nonce_hex: %v", err)
			}
			if len(nonce) != 12 {
				t.Fatalf("Expected nonce length 12, got %d", len(nonce))
			}

			aad, err := hex.DecodeString(tc.AadHex)
			if err != nil {
				t.Fatalf("Invalid aad_hex: %v", err)
			}

			plaintext, err := hex.DecodeString(tc.PlaintextHex)
			if err != nil {
				t.Fatalf("Invalid plaintext_hex: %v", err)
			}

			expectedCiphertextAndTag, err := hex.DecodeString(tc.ExpectedCiphertextAndTagHex)
			if err != nil {
				t.Fatalf("Invalid expected_ciphertext_and_tag_hex: %v", err)
			}

			expectedTag, err := hex.DecodeString(tc.ExpectedTagHex)
			if err != nil {
				t.Fatalf("Invalid expected_tag_hex: %v", err)
			}
			if len(expectedTag) != 16 {
				t.Fatalf("Expected tag length 16, got %d", len(expectedTag))
			}

			block, err := aes.NewCipher(key)
			if err != nil {
				t.Fatalf("Failed to create AES cipher: %v", err)
			}

			// Note: cipher.NewGCM defaults to 12-byte nonce and 16-byte tag length.
			aesgcm, err := cipher.NewGCM(block)
			if err != nil {
				t.Fatalf("Failed to create GCM: %v", err)
			}

			// Go's cipher.AEAD.Seal appends the authentication tag to the ciphertext.
			// Resulting layout is "ciphertext || tag", matching expected_ciphertext_and_tag_hex.
			sealed := aesgcm.Seal(nil, nonce, plaintext, aad)

			if tc.Valid {
				// Positive case: Encrypt and verify byte-for-byte match.
				if hex.EncodeToString(sealed) != tc.ExpectedCiphertextAndTagHex {
					t.Errorf("Encryption mismatch. Expected %s, got %s", tc.ExpectedCiphertextAndTagHex, hex.EncodeToString(sealed))
				}

				// Also try to decrypt to verify correctness
				opened, err := aesgcm.Open(nil, nonce, expectedCiphertextAndTag, aad)
				if err != nil {
					t.Errorf("Decryption failed for valid case: %v", err)
				}
				if hex.EncodeToString(opened) != tc.PlaintextHex {
					t.Errorf("Decrypted plaintext mismatch. Expected %s, got %s", tc.PlaintextHex, hex.EncodeToString(opened))
				}
			} else {
				// Negative case: The vector includes modified parameters (like altered tag/AAD).
				// We expect decryption to fail.
				_, err := aesgcm.Open(nil, nonce, expectedCiphertextAndTag, aad)
				if err == nil {
					t.Errorf("Expected decryption to fail for invalid case %s, but it succeeded", tc.Name)
				}
			}
		})
	}
}
