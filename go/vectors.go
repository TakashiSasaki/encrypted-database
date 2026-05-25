package vault

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// getTestVectorsDir returns the path to the test-vectors directory.
// It checks the VAULT_TEST_VECTORS_DIR environment variable first,
// and falls back to "../test-vectors".
func getTestVectorsDir() (string, error) {
	dir := os.Getenv("VAULT_TEST_VECTORS_DIR")
	if dir == "" {
		dir = "../test-vectors"
	}

	info, err := os.Stat(dir)
	if err != nil {
		return "", fmt.Errorf("could not access test vectors directory '%s': %w", dir, err)
	}
	if !info.IsDir() {
		return "", fmt.Errorf("path '%s' is not a directory", dir)
	}

	return dir, nil
}

// loadJSONVector reads and parses a JSON file from the given relative path within the test vectors directory.
func loadJSONVector(relPath string, v interface{}) error {
	baseDir, err := getTestVectorsDir()
	if err != nil {
		return err
	}

	fullPath := filepath.Join(baseDir, relPath)
	data, err := os.ReadFile(fullPath)
	if err != nil {
		return fmt.Errorf("could not read test vector file '%s': %w", fullPath, err)
	}

	if err := json.Unmarshal(data, v); err != nil {
		return fmt.Errorf("failed to parse JSON in file '%s': %w", fullPath, err)
	}

	return nil
}
