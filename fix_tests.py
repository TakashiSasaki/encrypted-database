import re

# Update go/payload_test.go to add explicit mismatch assertion for negative tests
with open("go/payload_test.go", "r") as f:
    go_content = f.read()

go_mismatch_code = """
				if valid {
					if string(expectedAad) != string(reconstructedAad) {
						t.Fatalf("reconstructed AAD does not match expected_aad_hex\\nExpected: %x\\nGot:      %x", expectedAad, reconstructedAad)
					}
				} else {
					if string(expectedAad) == string(reconstructedAad) {
						t.Fatalf("expected reconstructed AAD to mismatch expected_aad_hex for negative vector, but they matched")
					}
				}
"""

go_content = re.sub(
    r'if valid {\n\s*if string\(expectedAad\) != string\(reconstructedAad\) {\n\s*t\.Fatalf\("reconstructed AAD does not match expected_aad_hex\\nExpected: %x\\nGot:      %x", expectedAad, reconstructedAad\)\n\s*}\n\s*}',
    go_mismatch_code.strip(),
    go_content
)

# And fix the unchecked interface assertion:
go_content = re.sub(
    r'var vecs \[\]map\[string\]interface\{\}\n\s*err := vectors\.LoadJSONVector\("payload/payload-encryption-v1\.json", &vecs\)',
    r'''type PayloadVector struct {
		Name                       string                 `json:"name"`
		Description                string                 `json:"description,omitempty"`
		Valid                      bool                   `json:"valid"`
		ObjectUUID                 *string                `json:"object_uuid"`
		SchemaUUID                 *string                `json:"schema_uuid"`
		ContentType                *string                `json:"content_type"`
		Kid                        *string                `json:"kid"`
		Alg                        *string                `json:"alg"`
		RecordDekHex               *string                `json:"record_dek_hex"`
		NonceHex                   *string                `json:"nonce_hex"`
		PayloadJSON                interface{}            `json:"payload_json"`
		ExpectedPayloadJcsHex      *string                `json:"expected_payload_jcs_hex"`
		ExpectedAadHex             *string                `json:"expected_aad_hex"`
		ExpectedCiphertextHex      *string                `json:"expected_ciphertext_hex"`
		ExpectedTagHex             *string                `json:"expected_tag_hex"`
		ExpectedCiphertextAndTagHex *string               `json:"expected_ciphertext_and_tag_hex"`
	}
	var vecs []PayloadVector
	err := vectors.LoadJSONVector("payload/payload-encryption-v1.json", &vecs)''',
    go_content
)

with open("go/payload_test.go", "w") as f:
    f.write(go_content)
