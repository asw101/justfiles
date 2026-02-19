# List available recipes
default:
    @just --list

# Show shell alias commands for all justfiles in this repo
alias:
    #!/usr/bin/env bash
    root="$(cd "$(dirname "{{justfile()}}")" && pwd)"
    for jf in "$root"/*/Justfile; do
        name="$(basename "$(dirname "$jf")")"
        echo "alias ${name}='just --justfile ${jf}'"
    done
