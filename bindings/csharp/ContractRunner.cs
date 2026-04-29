using System.Diagnostics;

namespace LifecourseContract;

public static class ContractRunner
{
    public const string CoreSchemaDirRelative = "specs/core-api/schemas/v1";
    public const string CoreFixtureDirRelative = "specs/core-api/fixtures/v1";

    public static ProcessStartInfo BuildProcessStartInfo(string requestPath, string? outputPath)
    {
        var arguments = $"-m lifecourse.model_contract --request {requestPath}";
        if (!string.IsNullOrWhiteSpace(outputPath))
        {
            arguments += $" --output {outputPath}";
        }

        return new ProcessStartInfo
        {
            FileName = "python3",
            Arguments = arguments,
            UseShellExecute = false,
            RedirectStandardOutput = false,
            RedirectStandardError = false,
        };
    }

    public static int Run(string[] args)
    {
        string? requestPath = null;
        string? outputPath = null;

        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--request" when index + 1 < args.Length:
                    requestPath = args[++index];
                    break;
                case "--output" when index + 1 < args.Length:
                    outputPath = args[++index];
                    break;
            }
        }

        if (string.IsNullOrWhiteSpace(requestPath))
        {
            Console.Error.WriteLine("--request is required");
            return 2;
        }

        var startInfo = BuildProcessStartInfo(requestPath, outputPath);
        using var process = Process.Start(startInfo);
        if (process is null)
        {
            Console.Error.WriteLine("Failed to start python3");
            return 1;
        }

        process.WaitForExit();
        return process.ExitCode;
    }
}
