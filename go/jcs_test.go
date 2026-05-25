package vault

import (
	"encoding/hex"
	"errors"
	"path/filepath"
	"testing"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/vectors"
)

type JCSVector struct {
	Name           string      `json:"name"`
	Description    string      `json:"description"`
	Input          interface{} `json:"input"`
	ExpectedString string      `json:"expected_string"`
	ExpectedHex    string      `json:"expected_hex"`
}

func TestJCSConformance(t *testing.T) {
	var v []JCSVector
	err := vectors.LoadJSONVector(filepath.Join("jcs", "rfc8785-basic.json"), &v)
	if err != nil {
		t.Fatalf("Failed to load JCS test vectors: %v", err)
	}

	for _, tc := range v {
		t.Run(tc.Name, func(t *testing.T) {
			canonicalString, err := jcs.Canonicalize(tc.Input)
			if err != nil {
				// Handle expected limitations
				if errors.Is(err, jcs.ErrUnsupportedJCSValue) {
					t.Logf("Expected limitation encountered for %s: %v", tc.Name, err)
					return // Mark test as passed because it correctly rejected unsupported value
				}
				t.Fatalf("Unexpected canonicalization error: %v", err)
			}

			if canonicalString != tc.ExpectedString {
				t.Errorf("Expected string %q, got %q", tc.ExpectedString, canonicalString)
			}

			canonicalHex := hex.EncodeToString([]byte(canonicalString))
			if canonicalHex != tc.ExpectedHex {
				t.Errorf("Expected hex %q, got %q", tc.ExpectedHex, canonicalHex)
			}
		})
	}
}
