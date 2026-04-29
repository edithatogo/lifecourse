test_that("run_contract builds a contract-first invocation", {
  request <- file.path("..", "..", "..", "..", "specs", "core-api", "fixtures", "v1", "model-run-request.fixture.json")
  expect_true(file.exists(request))
  expect_silent(run_contract(request_path = request, python = "python3"))
})
