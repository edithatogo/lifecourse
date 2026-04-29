use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;

pub const CORE_SCHEMA_DIR_RELATIVE: &str = "specs/core-api/schemas/v1";
pub const CORE_FIXTURE_DIR_RELATIVE: &str = "specs/core-api/fixtures/v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ModelRunRequest {
    pub contract_version: String,
    pub request_id: String,
    pub model_id: String,
    pub parameter_set: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ContractPaths {
    pub repo_root: PathBuf,
    pub schema_dir: PathBuf,
    pub fixture_dir: PathBuf,
    pub request_fixture: PathBuf,
}

pub fn contract_paths(repo_root: impl Into<PathBuf>) -> ContractPaths {
    let repo_root = repo_root.into();
    ContractPaths {
        schema_dir: repo_root.join(CORE_SCHEMA_DIR_RELATIVE),
        fixture_dir: repo_root.join(CORE_FIXTURE_DIR_RELATIVE),
        request_fixture: repo_root.join(CORE_FIXTURE_DIR_RELATIVE).join("model-run-request.fixture.json"),
        repo_root,
    }
}

pub fn build_command(request_path: impl AsRef<std::ffi::OsStr>, output_path: Option<impl AsRef<std::ffi::OsStr>>) -> Command {
    let mut command = Command::new("python3");
    command.arg("-m").arg("lifecourse.model_contract").arg("--request").arg(request_path);
    if let Some(output_path) = output_path {
        command.arg("--output").arg(output_path);
    }
    command
}
