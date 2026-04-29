package contract

import (
	"strings"
	"path/filepath"
	"testing"
)

func TestPathsReferenceCoreApiArtifacts(t *testing.T) {
	paths, err := Paths()
	if err != nil {
		t.Fatalf("paths: %v", err)
	}

	if !strings.Contains(paths.SchemaDir, CoreSchemaDirRelative) {
		t.Fatalf("schema dir mismatch: %s", paths.SchemaDir)
	}
	if !strings.Contains(paths.FixtureDir, CoreFixtureDirRelative) {
		t.Fatalf("fixture dir mismatch: %s", paths.FixtureDir)
	}
}

func TestBuildCommandUsesPythonContractModule(t *testing.T) {
	cmd := BuildCommand("request.json", "response.json")

	if filepath.Base(cmd.Path) != "python3" {
		t.Fatalf("expected python3, got %s", cmd.Path)
	}

	args := strings.Join(cmd.Args, " ")
	if !strings.Contains(args, "-m lifecourse.model_contract") {
		t.Fatalf("expected contract module invocation, got %s", args)
	}
	if !strings.Contains(args, "--request request.json") {
		t.Fatalf("expected request argument, got %s", args)
	}
	if !strings.Contains(args, "--output response.json") {
		t.Fatalf("expected output argument, got %s", args)
	}
}
