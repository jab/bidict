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
          packages = with pkgs; [
            pre-commit
            python312
            python311
            python310
            python39
            pypy310
            pypy39
          ];
          shellHook = ''
            export HYPOTHESIS_EXPERIMENTAL_OBSERVABILITY=1
            source ./dev-deps/dev.env
            if test -e "$VENV_SUBDIR"; then
              echo "* Using pre-existing development virtualenv dir ($VENV_SUBDIR)"
            else
              echo "* No pre-existing development virtualenv dir ($VENV_SUBDIR), initializing..."
              ./init_dev_env
            fi
            source "$VENV_SUBDIR/bin/activate"
            echo "* Activated development virtualenv ($VENV_SUBDIR)"
          '';
        };
      });
    };
}
