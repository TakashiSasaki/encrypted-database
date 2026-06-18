package work.moukaeritai.vault;

import java.util.regex.Pattern;

public class ScaffoldValidators {

    private static final Pattern UUID_PATTERN = Pattern.compile(
        "^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    );

    public static boolean isValidUuid(String uuid) {
        if (uuid == null) return false;
        return UUID_PATTERN.matcher(uuid).matches();
    }

    public static boolean isValidContentType(String contentType) {
        if (contentType == null || contentType.isEmpty()) return false;

        int slashIndex = contentType.indexOf('/');
        if (slashIndex == -1 || slashIndex != contentType.lastIndexOf('/')) {
            return false;
        }

        String beforeSlash = contentType.substring(0, slashIndex);
        String afterSlash = contentType.substring(slashIndex + 1);

        if (beforeSlash.isEmpty() || afterSlash.isEmpty()) {
            return false;
        }

        for (int i = 0; i < contentType.length(); i++) {
            char c = contentType.charAt(i);
            if (c < 0x20 || c == 0x7F) {
                return false;
            }
        }

        return true;
    }

    public static boolean isValidMetadata(String metadata) {
        if (metadata == null) return false;
        return !metadata.trim().isEmpty();
    }
}
