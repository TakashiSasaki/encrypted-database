pub mod aad;
pub mod base64url;
pub mod jcs;
pub mod sqlitev1;
pub mod sqlitev1_reader;
pub mod sqlitev1_writer;
pub mod vectors;

// Export ReadOnlyReader and its error types as a public API,
// noting that it is an experimental portability scaffold.
pub use sqlitev1_reader::{ReadOnlyReader, ReaderError, open_read_only};
pub use sqlitev1_writer::{Writer, WriterError, create_new};
