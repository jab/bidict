{
  description = "bidict";

  # Flake inputs
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
  };

  # Flake outputs
  outputs = { self, nixpkgs }:
    let
      # Systems supported
      allSystems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];

      # Helper to provide system-specific attributes
      nameValuePair = name: value: { inherit name value; };
      genAttrs = names: f: builtins.listToAttrs (map (n: nameValuePair n (f n)) names);
      forAllSystems = f: genAttrs allSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      # Development environment output
      devShells = forAllSystems ({ pkgs }: {
        default = pkgs.mkShell {
          packages = [
            pkgs.pre-commit
            pkgs.python312
            pkgs.python311Packages.pip
            pkgs.python311Packages.tox
            pkgs.python311
            pkgs.python310
            pkgs.python39
            pkgs.python38
            pkgs.pypy38
            # pypy38 provides no "pypy3.8" executable.
            # pypy39 must go after pypy38 so that pypy3 resolves to pypy3.8 via PATH,
            # ensuring there is still a way to invoke pypy3.8 other than by absolute path.
            pkgs.pypy39
          ];
          # See comment above. Not possible to add a shell alias, but at least export an env var:
          PYPY38 = "${pkgs.pypy38}/bin/pypy3";
          shellHook = ''
            if ! test -e .venv; then
              python3.11 -m venv --upgrade-deps .venv/dev
              .venv/dev/bin/pip install -r dev-deps/python3.11/test.txt -r dev-deps/python3.11/dev.txt
              .venv/dev/bin/pip install -e .
            fi
            source .venv/dev/bin/activate
          '';
        };
      });
    };
}
