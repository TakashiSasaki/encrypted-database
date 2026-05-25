package base64url

import (
	"encoding/base64"
	"errors"
	"strings"
)

// DecodeStrict decodes a base64url encoded string without padding.
// It strictly rejects strings containing '=' padding characters or invalid URL-safe characters.
func DecodeStrict(s string) ([]byte, error) {
	if strings.Contains(s, "=") {
		return nil, errors.New("base64url string contains '=' padding, which is not allowed")
	}

	decoded, err := base64.RawURLEncoding.DecodeString(s)
	if err != nil {
		return nil, err
	}

	return decoded, nil
}
