package vectors

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// GetTestVectorsDir returns the path to the test-vectors directory.
// It checks the VAULT_TEST_VECTORS_DIR environment variable first,
// and falls back to "../test-vectors".
func GetTestVectorsDir() (string, error) {
	dir := os.Getenv("VAULT_TEST_VECTORS_DIR")
	if dir == "" {
		// When running tests, the working directory is the package directory.
		// If running from internal/vectors, it's go/internal/vectors.
		// Let's resolve upwards until we find test-vectors or hit root.
		cwd, err := os.Getwd()
		if err != nil {
			return "", err
		}

		// Simple search upwards
		for i := 0; i < 5; i++ {
			candidate := filepath.Join(cwd, "test-vectors")
			if info, err := os.Stat(candidate); err == nil && info.IsDir() {
				return candidate, nil
			}
			candidate2 := filepath.Join(cwd, "../test-vectors")
			if info, err := os.Stat(candidate2); err == nil && info.IsDir() {
				return candidate2, nil
			}
			cwd = filepath.Dir(cwd)
			if cwd == "/" || strings.HasSuffix(cwd, ":\\") {
				break
			}
		}
		dir = "../test-vectors" // Fallback
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

// LoadJSONVector reads and parses a JSON file from the given relative path within the test vectors directory.
func LoadJSONVector(relPath string, v interface{}) error {
	baseDir, err := GetTestVectorsDir()
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
