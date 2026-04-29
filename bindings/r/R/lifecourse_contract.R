run_contract <- function(request_path, output_path = NULL, python = "python3") {
  if (!file.exists(request_path)) {
    stop(paste0("request_path not found: ", request_path), call. = FALSE)
  }

  args <- c("-m", "lifecourse.model_contract", "--request", request_path)
  if (!is.null(output_path)) {
    args <- c(args, "--output", output_path)
  }

  result <- system2(python, args, stdout = TRUE, stderr = TRUE)
  if (!is.null(attr(result, "status"))) {
    stop(paste(result, collapse = "\n"), call. = FALSE)
  }

  invisible(result)
}
