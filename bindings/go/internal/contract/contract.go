package contract

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

const (
	CoreSchemaDirRelative  = "specs/core-api/schemas/v1"
	CoreFixtureDirRelative = "specs/core-api/fixtures/v1"
	PythonModule           = "lifecourse.model_contract"
)

type ModelRunRequest struct {
	ContractVersion string `json:"contract_version"`
	RequestID       string `json:"request_id"`
	ModelID         string `json:"model_id"`
	ParameterSet    string `json:"parameter_set"`
}

type ContractPaths struct {
	RepoRoot    string
	SchemaDir   string
	FixtureDir  string
	RequestPath string
}

func RepoRoot() (string, error) {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		return "", fmt.Errorf("resolve repo root: caller information unavailable")
	}

	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", "..", "..", "..")), nil
}

func Paths() (ContractPaths, error) {
	root, err := RepoRoot()
	if err != nil {
		return ContractPaths{}, err
	}

	return ContractPaths{
		RepoRoot:    root,
		SchemaDir:   filepath.Join(root, CoreSchemaDirRelative),
		FixtureDir:  filepath.Join(root, CoreFixtureDirRelative),
		RequestPath: filepath.Join(root, CoreFixtureDirRelative, "model-run-request.fixture.json"),
	}, nil
}

func LoadRequest(path string) (ModelRunRequest, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return ModelRunRequest{}, err
	}

	var request ModelRunRequest
	if err := json.Unmarshal(content, &request); err != nil {
		return ModelRunRequest{}, err
	}

	return request, nil
}

func BuildCommand(requestPath string, outputPath string) *exec.Cmd {
	args := []string{"-m", PythonModule, "--request", requestPath}
	if outputPath != "" {
		args = append(args, "--output", outputPath)
	}
	return exec.Command("python3", args...)
}

func Run(requestPath string, outputPath string) error {
	cmd := BuildCommand(requestPath, outputPath)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
