use std::env;
use std::process;
use vault_moukaeritai_work::sqlitev1_writer::open_writer;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        eprintln!(
            "Usage: {} <db_path> <passphrase> <object_uuid>",
            args[0]
        );
        process::exit(1);
    }

    let db_path = std::path::Path::new(&args[1]);
    let passphrase = &args[2];
    let object_uuid = &args[3];

    let mut writer = match open_writer(db_path, passphrase) {
        Ok(w) => w,
        Err(e) => {
            eprintln!("Failed to open DB: {}", e);
            process::exit(1);
        }
    };

    if let Err(e) = writer.delete_payload(object_uuid) {
        eprintln!("Failed to delete payload: {}", e);
        process::exit(1);
    }
}
