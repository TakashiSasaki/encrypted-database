use std::env;
use std::process;
use vault_moukaeritai_work::jcs::canonicalize;
use vault_moukaeritai_work::sqlitev1_writer::create_new;

#[derive(serde::Serialize)]
struct FixtureOutput {
    object_uuid: String,
    initial_payload_hex: String,
    updated_payload_hex: String,
    deleted: bool,
}

fn to_hex(s: &str) -> String {
    s.as_bytes().iter().map(|b| format!("{:02x}", b)).collect()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 8 {
        eprintln!(
            "Usage: {} <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a_json> <payload_b_json> [mode:update_only|update_delete]",
            args[0]
        );
        process::exit(1);
    }

    let db_path = std::path::Path::new(&args[1]);
    let passphrase = &args[2];
    let platform = &args[3];
    let schema_uuid = &args[4];
    let content_type = &args[5];
    let payload_a: serde_json::Value =
        serde_json::from_str(&args[6]).expect("payload A JSON parse");
    let payload_b: serde_json::Value =
        serde_json::from_str(&args[7]).expect("payload B JSON parse");
    let mode = args.get(8).map(|s| s.as_str()).unwrap_or("update_delete");
    if mode != "update_only" && mode != "update_delete" {
        eprintln!("invalid mode: {}", mode);
        process::exit(1);
    }

    let mut writer = create_new(db_path, passphrase, platform).expect("create DB");
    let object_uuid = writer
        .store_payload(schema_uuid, content_type, &payload_a)
        .expect("store payload A");
    writer
        .update_payload(&object_uuid, schema_uuid, content_type, &payload_b)
        .expect("update payload B");

    let deleted = if mode == "update_delete" {
        writer.delete_payload(&object_uuid).expect("delete payload");
        true
    } else {
        false
    };

    let out = FixtureOutput {
        object_uuid,
        initial_payload_hex: to_hex(&canonicalize(&payload_a).expect("canonicalize A")),
        updated_payload_hex: to_hex(&canonicalize(&payload_b).expect("canonicalize B")),
        deleted,
    };
    println!("{}", serde_json::to_string(&out).expect("serialize output"));
}
