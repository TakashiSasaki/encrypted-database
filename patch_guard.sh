cat << 'PATCH' > /tmp/guard.patch
--- c/src/vault_jcs_model.c
+++ c/src/vault_jcs_model.c
@@ -75,6 +75,9 @@
         return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
     }

+    if (count > SIZE_MAX / sizeof(VaultJcsModelValue)) {
+        return VAULT_JCS_MODEL_ERROR_MEMORY;
+    }
     VaultJcsModelValue* copy = NULL;
     if (count > 0) {
         copy = (VaultJcsModelValue*)malloc(count * sizeof(VaultJcsModelValue));
@@ -120,6 +123,9 @@
         }
     }

+    if (count > SIZE_MAX / sizeof(VaultJcsModelObjectMember)) {
+        return VAULT_JCS_MODEL_ERROR_MEMORY;
+    }
     VaultJcsModelObjectMember* copy = NULL;
     if (count > 0) {
         copy = (VaultJcsModelObjectMember*)malloc(count * sizeof(VaultJcsModelObjectMember));
PATCH
patch -p0 < /tmp/guard.patch
