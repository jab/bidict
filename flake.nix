{
  description = "bidict";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
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
