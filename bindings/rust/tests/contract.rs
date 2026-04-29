use lifecourse_contract::{build_command, contract_paths, CORE_FIXTURE_DIR_RELATIVE, CORE_SCHEMA_DIR_RELATIVE};

#[test]
fn command_uses_python_contract_module() {
    let command = build_command("request.json", Some("response.json"));
    let args = command
        .get_args()
        .map(|arg| arg.to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join(" ");

    assert_eq!(command.get_program().to_string_lossy(), "python3");
    assert!(args.contains("-m lifecourse.model_contract"));
    assert!(args.contains("--request request.json"));
    assert!(args.contains("--output response.json"));
}

#[test]
fn contract_paths_point_at_shared_artifacts() {
    let paths = contract_paths("/repo");

    assert_eq!(paths.schema_dir.to_string_lossy(), format!("/repo/{CORE_SCHEMA_DIR_RELATIVE}"));
    assert_eq!(paths.fixture_dir.to_string_lossy(), format!("/repo/{CORE_FIXTURE_DIR_RELATIVE}"));
    assert!(paths.request_fixture.to_string_lossy().ends_with("model-run-request.fixture.json"));
}
