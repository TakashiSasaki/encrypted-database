package work.moukaeritai.vault;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class ScaffoldValidatorsTest {

    @Test
    public void testValidUuid() {
        assertTrue(ScaffoldValidators.isValidUuid("123e4567-e89b-12d3-a456-426614174000"));
    }

    @Test
    public void testUppercaseUuidRejected() {
        assertFalse(ScaffoldValidators.isValidUuid("123E4567-E89B-12D3-A456-426614174000"));
    }

    @Test
    public void testInvalidVariantRejected() {
        assertFalse(ScaffoldValidators.isValidUuid("123e4567-e89b-12d3-c456-426614174000"));
    }

    @Test
    public void testInvalidVersionRejected() {
        assertFalse(ScaffoldValidators.isValidUuid("123e4567-e89b-02d3-a456-426614174000"));
    }

    @Test
    public void testMissingHyphensRejected() {
        assertFalse(ScaffoldValidators.isValidUuid("123e4567e89b12d3a456426614174000"));
    }

    @Test
    public void testValidContentType() {
        assertTrue(ScaffoldValidators.isValidContentType("application/json"));
    }

    @Test
    public void testContentTypeZeroSlashRejected() {
        assertFalse(ScaffoldValidators.isValidContentType("applicationjson"));
    }

    @Test
    public void testContentTypeTwoSlashesRejected() {
        assertFalse(ScaffoldValidators.isValidContentType("application/json/text"));
    }

    @Test
    public void testContentTypeEmptyPartRejected() {
        assertFalse(ScaffoldValidators.isValidContentType("/json"));
        assertFalse(ScaffoldValidators.isValidContentType("application/"));
    }

    @Test
    public void testContentTypeControlByteRejected() {
        assertFalse(ScaffoldValidators.isValidContentType("application/\njson"));
        assertFalse(ScaffoldValidators.isValidContentType("application/\tjson"));
    }

    @Test
    public void testContentTypeDelRejected() {
        assertFalse(ScaffoldValidators.isValidContentType("application/json\u007F"));
    }

    @Test
    public void testMetadataWhitespaceOnlyRejected() {
        assertFalse(ScaffoldValidators.isValidMetadata("\u2003"));
        assertFalse(ScaffoldValidators.isValidMetadata("   "));
        assertFalse(ScaffoldValidators.isValidMetadata("\t\n"));
    }

    @Test
    public void testValidMetadata() {
        assertTrue(ScaffoldValidators.isValidMetadata("valid-metadata"));
    }
}
