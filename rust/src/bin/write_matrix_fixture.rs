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

fn fail(msg: &str) -> ! {
    eprintln!("{}", msg);
    process::exit(1);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 8 {
        fail(&format!(
            "Usage: {} <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a_json> <payload_b_json> [mode:update_only|update_delete]",
            args[0]
        ));
    }

    let db_path = std::path::Path::new(&args[1]);
    let passphrase = &args[2];
    let platform = &args[3];
    let schema_uuid = &args[4];
    let content_type = &args[5];
    let payload_a: serde_json::Value = match serde_json::from_str(&args[6]) {
        Ok(v) => v,
        Err(e) => fail(&format!("payload A parse error: {}", e)),
    };
    let payload_b: serde_json::Value = match serde_json::from_str(&args[7]) {
        Ok(v) => v,
        Err(e) => fail(&format!("payload B parse error: {}", e)),
    };

    let mode = args.get(8).map(|s| s.as_str()).unwrap_or("update_delete");
    if mode != "update_only" && mode != "update_delete" {
        fail(&format!("invalid mode: {}", mode));
    }

    let mut writer = match create_new(db_path, passphrase, platform) {
        Ok(w) => w,
        Err(e) => fail(&format!("create DB error: {}", e)),
    };

    let object_uuid = match writer.store_payload(schema_uuid, content_type, &payload_a) {
        Ok(v) => v,
        Err(e) => fail(&format!("store error: {}", e)),
    };

    if let Err(e) = writer.update_payload(&object_uuid, schema_uuid, content_type, &payload_b) {
        fail(&format!("update error: {}", e));
    }

    let deleted = if mode == "update_delete" {
        if let Err(e) = writer.delete_payload(&object_uuid) {
            fail(&format!("delete error: {}", e));
        }
        true
    } else {
        false
    };

    let initial_payload_hex = match canonicalize(&payload_a) {
        Ok(v) => to_hex(&v),
        Err(e) => fail(&format!("canonicalize A error: {}", e)),
    };
    let updated_payload_hex = match canonicalize(&payload_b) {
        Ok(v) => to_hex(&v),
        Err(e) => fail(&format!("canonicalize B error: {}", e)),
    };

    let out = FixtureOutput {
        object_uuid,
        initial_payload_hex,
        updated_payload_hex,
        deleted,
    };

    match serde_json::to_string(&out) {
        Ok(s) => println!("{}", s),
        Err(e) => fail(&format!("output encode error: {}", e)),
    }
}
