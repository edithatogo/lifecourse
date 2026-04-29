import assert from "node:assert/strict";
import test from "node:test";

import {
  buildContractCommand,
  coreArtifactPaths,
  coreFixtureDirRelative,
  coreSchemaDirRelative,
  pythonModule,
} from "../src/index.js";

test("buildContractCommand invokes the Python reference contract", () => {
  const command = buildContractCommand({
    requestPath: "fixtures/model-run-request.fixture.json",
    outputPath: "fixtures/model-run-response.fixture.json",
  });

  assert.equal(command.command, "python3");
  assert.deepEqual(command.args.slice(0, 2), ["-m", pythonModule]);
  assert.ok(command.args.includes("--request"));
  assert.ok(command.args.includes("fixtures/model-run-request.fixture.json"));
  assert.ok(command.args.includes("--output"));
});

test("coreArtifactPaths points at the shared contract directories", () => {
  const paths = coreArtifactPaths("/repo");

  assert.equal(paths.schemaDir, "/repo/" + coreSchemaDirRelative);
  assert.equal(paths.fixtureDir, "/repo/" + coreFixtureDirRelative);
  assert.ok(paths.requestFixture.endsWith("model-run-request.fixture.json"));
});
