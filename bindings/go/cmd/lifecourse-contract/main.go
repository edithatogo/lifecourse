package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/edithatogo/lifecourse/bindings/go/internal/contract"
)

func main() {
	requestPath := flag.String("request", "", "Path to a model run request JSON file.")
	outputPath := flag.String("output", "", "Optional path for the response JSON file.")
	flag.Parse()

	if *requestPath == "" {
		fmt.Fprintln(os.Stderr, "--request is required")
		os.Exit(2)
	}

	if err := contract.Run(*requestPath, *outputPath); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
