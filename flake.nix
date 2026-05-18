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
      devShells = {
        default = pkgs.mkShell {
          packages = with pkgs; [
            prek
            python314
            python313
            python312
            python311
            pypy3
            uv  # Bootstrap version used to install a possibly-newer version when 'uv sync' is run (via uv.lock)
          ];
          shellHook = ''
            ./init_dev_env
            source ".venv/bin/activate"
          '';
        };
        lint = pkgs.mkShell {
          packages = with pkgs; [prek];
        };
        update_deps = pkgs.mkShell {
          packages = with pkgs; [prek uv];
        };
      };
    });
}
