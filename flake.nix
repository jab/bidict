{
  description = "bidict";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs";
  };

  outputs = { self, flake-utils, nixpkgs }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };
    in {
      devShell = pkgs.mkShell {
        packages = with pkgs; [
          pre-commit
          python314
          python313
          python312
          python311
          python310
          pypy310
          uv  # Bootstrap version used to install a possibly-newer version when 'uv sync' is run (via uv.lock)
        ];
        shellHook = ''
          ./init_dev_env
          source ".venv/bin/activate"
        '';
      };
    });
}
