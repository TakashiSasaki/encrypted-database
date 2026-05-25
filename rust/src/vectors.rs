use std::env;
use std::path::{Path, PathBuf};

/// Resolves the path to the `test-vectors` directory.
///
/// It checks the `VAULT_TEST_VECTORS_DIR` environment variable first,
/// falling back to `../test-vectors`.
pub fn test_vectors_dir() -> Result<PathBuf, String> {
    let dir = env::var("VAULT_TEST_VECTORS_DIR").unwrap_or_else(|_| "../test-vectors".to_string());

    let path = PathBuf::from(&dir);
    if !path.exists() {
        return Err(format!("Test vectors directory does not exist at {:?}", path));
    }
    if !path.is_dir() {
        return Err(format!("Path {:?} is not a directory", path));
    }

    Ok(path)
}

/// Helper function to build a full path to a specific test vector file.
pub fn test_vector_path(rel_path: impl AsRef<Path>) -> Result<PathBuf, String> {
    let base_dir = test_vectors_dir()?;
    let full_path = base_dir.join(rel_path);

    if !full_path.exists() {
        return Err(format!("Test vector file does not exist at {:?}", full_path));
    }

    Ok(full_path)
}
