{
  description = "bidict";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    python38.url = "github:NixOS/nixpkgs/9a9dae8f6319600fa9aebde37f340975cab4b8c0";
  };

  outputs = { self, nixpkgs, flake-utils, python38 }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };
    in {
      devShell = pkgs.mkShell {
        packages = with pkgs; [
          pre-commit
          python312
          python311
          python310
          python39
          pypy310
          pypy39
          uv  # bootstrap uv version
        ] ++ [
          python38.legacyPackages.${system}.python38
        ];
        shellHook = ''
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
}
