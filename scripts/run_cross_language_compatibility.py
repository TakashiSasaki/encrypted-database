import os
import sys

LANGUAGES = {
    "python": {"read": True, "write": True, "stable_api": True},
    "nodejs": {"read": True, "write": True, "stable_api": True},
    "go": {"read": True, "write": True, "stable_api": False},
    "rust": {"read": True, "write": True, "stable_api": False},
    "zig": {"read": True, "write": True, "stable_api": False},
    "c": {"read": False, "write": False, "stable_api": False},
    "cpp": {"read": False, "write": False, "stable_api": False},
}

def main():
    print("Cross-Language Read/Write Compatibility Matrix")
    print("=" * 60)

    skipped_count = 0
    for writer in LANGUAGES.keys():
        for reader in LANGUAGES.keys():
            if not LANGUAGES[writer]["write"] or not LANGUAGES[writer]["stable_api"]:
                reason = "skipped (writer lacks stable API or write support)"
            elif not LANGUAGES[reader]["read"] or not LANGUAGES[reader]["stable_api"]:
                reason = "skipped (reader lacks stable API or read support)"
            else:
                reason = "skipped (not yet runnable)"

            print(f"{writer:10} (write) -> {reader:10} (read) : {reason}")
            skipped_count += 1

    print("\nSummary:")
    print("No implementations are currently runnable for cross-language compatibility tests.")

if __name__ == '__main__':
    main()
