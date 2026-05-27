use std::env;
use std::process;
use vault_moukaeritai_work::jcs::canonicalize;
use vault_moukaeritai_work::sqlitev1_writer::create_new;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 8 {
        eprintln!(
            "Usage: {} <mode> <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_json>",
            args[0]
        );
        process::exit(1);
    }

    let mode = &args[1];
    let db_path = std::path::Path::new(&args[2]);
    let passphrase = &args[3];
    let platform = &args[4];
    let schema_uuid = &args[5];
    let content_type = &args[6];
    let payload_str = &args[7];

    let mut payload: serde_json::Value = match serde_json::from_str(payload_str) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("Failed to parse payload JSON: {}", e);
            process::exit(1);
        }
    };

    let mut writer = match create_new(db_path, passphrase, platform) {
        Ok(w) => w,
        Err(e) => {
            eprintln!("Failed to create DB: {}", e);
            process::exit(1);
        }
    };

    let obj_uuid = match writer.store_payload(schema_uuid, content_type, &payload) {
        Ok(u) => u,
        Err(e) => {
            eprintln!("Failed to store payload: {}", e);
            process::exit(1);
        }
    };

    if mode == "update" {
        let payload2: serde_json::Value =
            serde_json::json!({"secret": "matrix-test", "value": 100, "updated": true});
        if let Err(e) = writer.update_payload(&obj_uuid, schema_uuid, content_type, &payload2) {
            eprintln!("Failed to update payload: {}", e);
            process::exit(1);
        }
        payload = payload2;
    } else if mode == "delete" {
        if let Err(e) = writer.delete_payload(&obj_uuid) {
            eprintln!("Failed to delete payload: {}", e);
            process::exit(1);
        }
        println!("{}\nDELETED", obj_uuid);
        return;
    }

    let expected_payload_jcs = match canonicalize(&payload) {
        Ok(jcs) => jcs,
        Err(e) => {
            eprintln!("Failed to canonicalize payload: {}", e);
            process::exit(1);
        }
    };

    let expected_payload_hex = expected_payload_jcs
        .as_bytes()
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect::<String>();

    println!("{}\n{}", obj_uuid, expected_payload_hex);
}
