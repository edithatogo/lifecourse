module LifecourseContract

using JSON

export run_contract

function run_contract(request_path::AbstractString; output_path::Union{Nothing,AbstractString}=nothing, python::AbstractString="python3")
    isfile(request_path) || error("request_path not found: $(request_path)")

    args = ["-m", "lifecourse.model_contract", "--request", request_path]
    if output_path !== nothing
        push!(args, "--output")
        push!(args, output_path)
    end

    cmd = `$(python) $(args...)`
    run(cmd)
    return nothing
end

end # module
