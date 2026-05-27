use std::env;
use std::process;
use vault_moukaeritai_work::sqlitev1_writer::open_writer;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 7 {
        eprintln!(
            "Usage: {} <db_path> <passphrase> <object_uuid> <schema_uuid> <content_type> <payload_json>",
            args[0]
        );
        process::exit(1);
    }

    let db_path = std::path::Path::new(&args[1]);
    let passphrase = &args[2];
    let object_uuid = &args[3];
    let schema_uuid = &args[4];
    let content_type = &args[5];
    let payload_str = &args[6];

    let payload: serde_json::Value = match serde_json::from_str(payload_str) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("Failed to parse payload JSON: {}", e);
            process::exit(1);
        }
    };

    let mut writer = match open_writer(db_path, passphrase) {
        Ok(w) => w,
        Err(e) => {
            eprintln!("Failed to open DB: {}", e);
            process::exit(1);
        }
    };

    if let Err(e) = writer.update_payload(object_uuid, schema_uuid, content_type, &payload) {
        eprintln!("Failed to update payload: {}", e);
        process::exit(1);
    }
}
