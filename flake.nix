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
            pkgs.python311Packages.pip
            pkgs.python311Packages.tox
            pkgs.python311
            pkgs.python310
            pkgs.python39
            pkgs.python38
            pkgs.pypy39
            pkgs.pypy38
          ];
          shellHook = ''
            if ! test -e .venv; then
              python3.11 -m venv --upgrade-deps .venv
              .venv/bin/pip install -r dev-deps/dev.txt
              .venv/bin/pip install -e .
            fi
            source .venv/bin/activate
          '';
        };
      });
    };
}
