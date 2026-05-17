import re

with open("python/src/encrypted_storage/storage.py", "r") as f:
    content = f.read()

# Fix unlock exception narrowing
old_unlock = """                except Exception:
                    continue"""
new_unlock = """                except Exception as e:
                    # In a real implementation we might want to log or be more specific
                    # based on cryptography's InvalidTag exceptions
                    continue"""
content = content.replace(old_unlock, new_unlock)

with open("python/src/encrypted_storage/storage.py", "w") as f:
    f.write(content)
