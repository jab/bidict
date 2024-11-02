{
  description = "bidict";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs";
    # Get pypy310 from a nixpkgs revision where its binary is in the binary cache
    # to avoid building it from source.
    pypy310.url = "github:NixOS/nixpkgs/d4f247e89f6e10120f911e2e2d2254a050d0f732";
  };

  outputs = { self, flake-utils, nixpkgs, pypy310 }:
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
          uv  # Bootstrap version used to install a possibly-newer version when 'uv sync' is run (via uv.lock)
        ] ++ [
          pypy310.legacyPackages.${system}.pypy310
        ];
        shellHook = ''
          ./init_dev_env
          source ".venv/bin/activate"
        '';
      };
    });
}
