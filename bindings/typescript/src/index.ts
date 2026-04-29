import path from "node:path";

export const coreSchemaDirRelative = "specs/core-api/schemas/v1";
export const coreFixtureDirRelative = "specs/core-api/fixtures/v1";
export const pythonModule = "lifecourse.model_contract";

export interface ContractInvocation {
  requestPath: string;
  outputPath?: string;
}

export function buildContractCommand(invocation: ContractInvocation): {
  command: string;
  args: string[];
} {
  const args = ["-m", pythonModule, "--request", invocation.requestPath];
  if (invocation.outputPath) {
    args.push("--output", invocation.outputPath);
  }

  return {
    command: "python3",
    args,
  };
}

export function coreArtifactPaths(repoRoot: string): {
  schemaDir: string;
  fixtureDir: string;
  requestFixture: string;
} {
  return {
    schemaDir: path.join(repoRoot, coreSchemaDirRelative),
    fixtureDir: path.join(repoRoot, coreFixtureDirRelative),
    requestFixture: path.join(repoRoot, coreFixtureDirRelative, "model-run-request.fixture.json"),
  };
}
