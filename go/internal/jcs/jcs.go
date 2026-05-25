package jcs

import (
	"bytes"
	"errors"
	"fmt"
	"math"
	"sort"
	"strconv"
	"strings"
	"unicode/utf16"
	"unicode/utf8"
)

// ErrUnsupportedJCSValue is returned when the canonicalizer encounters a value
// it does not support (e.g., specific number formats not yet handled).
var ErrUnsupportedJCSValue = errors.New("unsupported JCS value")

// Canonicalize returns the JCS (RFC 8785) canonicalized JSON string representation of v.
// NOTE: This is a minimal implementation targeting the scope of AAD test vectors
// and basic JCS validation. It may not fully support all edge cases of RFC 8785
// (e.g., complex floating point numbers).
func Canonicalize(v interface{}) (string, error) {
	switch val := v.(type) {
	case nil:
		return "null", nil
	case bool:
		if val {
			return "true", nil
		}
		return "false", nil
	case string:
		return serializeString(val)
	case int:
		return strconv.Itoa(val), nil
	case int64:
		return strconv.FormatInt(val, 10), nil
	case float64:
		if math.IsNaN(val) || math.IsInf(val, 0) {
			return "", fmt.Errorf("%w: NaN/Inf not supported by JSON", ErrUnsupportedJCSValue)
		}
		// In Go, default json.Marshal doesn't follow JCS for float64 exactly
		// (e.g., "1e+20"). However, for AAD vectors we might not even need float.
		// If it's an integer, format it as such.
		if val == math.Trunc(val) {
			return strconv.FormatFloat(val, 'f', 0, 64), nil
		}
		// For actual floats, we'll error out for now to satisfy "explicit limitation" requirement
		return "", fmt.Errorf("%w: fractional float formatting not fully implemented", ErrUnsupportedJCSValue)
	case []interface{}:
		var b bytes.Buffer
		b.WriteByte('[')
		for i, item := range val {
			if i > 0 {
				b.WriteByte(',')
			}
			itemStr, err := Canonicalize(item)
			if err != nil {
				return "", err
			}
			b.WriteString(itemStr)
		}
		b.WriteByte(']')
		return b.String(), nil
	case map[string]interface{}:
		keys := make([]string, 0, len(val))
		for k := range val {
			keys = append(keys, k)
		}
		// UTF-16 code unit ordering per RFC 8785
		sort.Slice(keys, func(i, j int) bool {
			return compareUTF16(keys[i], keys[j]) < 0
		})

		var b bytes.Buffer
		b.WriteByte('{')
		for i, k := range keys {
			if i > 0 {
				b.WriteByte(',')
			}
			kStr, err := serializeString(k)
			if err != nil {
				return "", err
			}
			b.WriteString(kStr)
			b.WriteByte(':')
			itemStr, err := Canonicalize(val[k])
			if err != nil {
				return "", err
			}
			b.WriteString(itemStr)
		}
		b.WriteByte('}')
		return b.String(), nil
	default:
		return "", fmt.Errorf("%w: unsupported type %T", ErrUnsupportedJCSValue, v)
	}
}

func compareUTF16(s1, s2 string) int {
	u1 := utf16.Encode([]rune(s1))
	u2 := utf16.Encode([]rune(s2))
	l1, l2 := len(u1), len(u2)
	l := l1
	if l2 < l {
		l = l2
	}
	for i := 0; i < l; i++ {
		if u1[i] < u2[i] {
			return -1
		} else if u1[i] > u2[i] {
			return 1
		}
	}
	if l1 < l2 {
		return -1
	} else if l1 > l2 {
		return 1
	}
	return 0
}

func serializeString(s string) (string, error) {
	var b strings.Builder
	b.WriteByte('"')
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError && size == 1 {
			return "", fmt.Errorf("%w: invalid UTF-8 in string", ErrUnsupportedJCSValue)
		}
		switch r {
		case '"':
			b.WriteString(`\"`)
		case '\\':
			b.WriteString(`\\`)
		case '\b':
			b.WriteString(`\b`)
		case '\f':
			b.WriteString(`\f`)
		case '\n':
			b.WriteString(`\n`)
		case '\r':
			b.WriteString(`\r`)
		case '\t':
			b.WriteString(`\t`)
		default:
			if r < 0x20 {
				b.WriteString(fmt.Sprintf(`\u%04x`, r))
			} else {
				b.WriteRune(r)
			}
		}
		i += size
	}
	b.WriteByte('"')
	return b.String(), nil
}
