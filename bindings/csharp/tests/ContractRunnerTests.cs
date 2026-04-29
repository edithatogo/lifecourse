using LifecourseContract;
using Xunit;

namespace LifecourseContract.Tests;

public sealed class ContractRunnerTests
{
    [Fact]
    public void BuildProcessStartInfoUsesPythonContractModule()
    {
        var startInfo = ContractRunner.BuildProcessStartInfo("request.json", "response.json");

        Assert.Equal("python3", startInfo.FileName);
        Assert.Contains("-m lifecourse.model_contract", startInfo.Arguments);
        Assert.Contains("--request request.json", startInfo.Arguments);
        Assert.Contains("--output response.json", startInfo.Arguments);
    }
}
