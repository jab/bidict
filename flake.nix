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
          python313
          python312
          python311
          python310
          python39
          pypy310
          pypy39
          uv  # bootstrap uv version (another version is installed in the dev env by this version)
        ];
        shellHook = ''
          ./init_dev_env
          source ".venv/bin/activate"
          echo "* Activated development virtualenv"
        '';
      };
    });
}
