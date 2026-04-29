using Test
using LifecourseContract

@testset "LifecourseContract" begin
    request = joinpath(@__DIR__, "..", "..", "..", "specs", "core-api", "fixtures", "v1", "model-run-request.fixture.json")
    @test isfile(request)
end
