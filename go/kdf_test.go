package vault

import (
	"encoding/hex"
	"math"
	"testing"

	"golang.org/x/crypto/argon2"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/base64url"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/vectors"
)

type Argon2idParameters struct {
	MemoryKiB   int `json:"memory_kib"`
	Iterations  int `json:"iterations"`
	Parallelism int `json:"parallelism"`
	SaltBytes   int `json:"salt_bytes"`
	OutputBytes int `json:"output_bytes"`
}

type Argon2idInput struct {
	Passphrase string `json:"passphrase"`
	SaltHex    string `json:"salt_hex,omitempty"`
	Salt       string `json:"salt,omitempty"`
}

type Argon2idTestCase struct {
	Profile           string             `json:"profile"`
	Description       string             `json:"description"`
	Parameters        Argon2idParameters `json:"parameters"`
	Input             Argon2idInput      `json:"input"`
	ExpectedOutputHex string             `json:"expected_output_hex"`
}

func TestArgon2idKdfVectors(t *testing.T) {
	var testCases []Argon2idTestCase
	err := vectors.LoadJSONVector("kdf/argon2id-v1.json", &testCases)
	if err != nil {
		t.Fatalf("Failed to load test vectors: %v", err)
	}

	for i, tc := range testCases {
		t.Run(tc.Description, func(t *testing.T) {
			if tc.Profile != "argon2id-profile-v1" {
				t.Fatalf("Unsupported profile: %s", tc.Profile)
			}

			// Validate and resolve salt
			hasHex := tc.Input.SaltHex != ""
			hasB64 := tc.Input.Salt != ""

			if hasHex && hasB64 {
				t.Fatalf("Test case %d: ambiguous input, both salt_hex and salt present", i)
			}
			if !hasHex && !hasB64 {
				t.Fatalf("Test case %d: missing salt", i)
			}

			var salt []byte
			if hasHex {
				salt, err = hex.DecodeString(tc.Input.SaltHex)
				if err != nil {
					t.Fatalf("Failed to decode salt_hex: %v", err)
				}
			} else {
				salt, err = base64url.DecodeStrict(tc.Input.Salt)
				if err != nil {
					t.Fatalf("Failed to decode strict base64url salt: %v", err)
				}
			}

			if len(salt) != tc.Parameters.SaltBytes {
				t.Fatalf("Decoded salt length (%d) does not match expected length (%d)", len(salt), tc.Parameters.SaltBytes)
			}

			// Parameter validation
			if tc.Parameters.Parallelism > math.MaxUint8 {
				t.Fatalf("Parallelism %d exceeds max uint8", tc.Parameters.Parallelism)
			}
			if tc.Parameters.OutputBytes > math.MaxUint32 {
				t.Fatalf("Output bytes %d exceeds max uint32", tc.Parameters.OutputBytes)
			}
			if tc.Parameters.Iterations > math.MaxUint32 {
				t.Fatalf("Iterations %d exceeds max uint32", tc.Parameters.Iterations)
			}
			if tc.Parameters.MemoryKiB > math.MaxUint32 {
				t.Fatalf("MemoryKiB %d exceeds max uint32", tc.Parameters.MemoryKiB)
			}

			passphraseBytes := []byte(tc.Input.Passphrase)

			// Run Argon2id
			derivedKey := argon2.IDKey(
				passphraseBytes,
				salt,
				uint32(tc.Parameters.Iterations),
				uint32(tc.Parameters.MemoryKiB),
				uint8(tc.Parameters.Parallelism),
				uint32(tc.Parameters.OutputBytes),
			)

			if len(derivedKey) != tc.Parameters.OutputBytes {
				t.Fatalf("Derived key length (%d) does not match expected length (%d)", len(derivedKey), tc.Parameters.OutputBytes)
			}

			derivedHex := hex.EncodeToString(derivedKey)
			if derivedHex != tc.ExpectedOutputHex {
				t.Fatalf("Derived key does not match expected output.\nGot: %s\nExp: %s", derivedHex, tc.ExpectedOutputHex)
			}
		})
	}
}
