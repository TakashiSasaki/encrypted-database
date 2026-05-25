package vault

import (
	"path/filepath"
	"testing"
)

// AADPolicyTestCase represents the minimal structure of an AAD test vector.
type AADPolicyTestCase struct {
	Name            string `json:"name"`
	Policy          string `json:"policy"`
	Description     string `json:"description"`
	ExpectedHex     string `json:"expected_hex"`
}

// AADTestVector represents the root array of AAD test vectors.
type AADTestVector []AADPolicyTestCase

func TestVectorsDirExists(t *testing.T) {
	dir, err := getTestVectorsDir()
	if err != nil {
		t.Fatalf("Test vectors directory must exist: %v", err)
	}
	t.Logf("Found test vectors directory at: %s", dir)
}

func TestLoadAADVectors(t *testing.T) {
	var vectors AADTestVector
	err := loadJSONVector(filepath.Join("aad", "aad-policies-v1.json"), &vectors)
	if err != nil {
		t.Fatalf("Failed to load AAD test vectors: %v", err)
	}

	if len(vectors) == 0 {
		t.Fatalf("Loaded AAD vectors but found no test cases (empty array)")
	}

	t.Logf("Successfully parsed %d AAD test vectors", len(vectors))
	for i, tc := range vectors {
		if tc.Name == "" {
			t.Errorf("Test case %d is missing a name", i)
		}
		if tc.Policy == "" {
			t.Errorf("Test case %d is missing a policy", i)
		}
	}
}
