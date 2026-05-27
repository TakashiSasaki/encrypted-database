fn main() {
    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let is_valid_uuid = schema_uuid.len() == 36
        && schema_uuid.chars().enumerate().all(|(i, c)| match i {
            8 | 13 | 18 | 23 => c == '-',
            14 => ('1'..='8').contains(&c),
            19 => ['8', '9', 'a', 'b'].contains(&c),
            _ => {
                let valid = c.is_ascii_hexdigit() && (c.is_ascii_lowercase() || c.is_ascii_digit());
                if !valid {
                    println!("Failed at {} char {}", i, c);
                }
                valid
            }
        });
    println!("Valid? {}", is_valid_uuid);
}
