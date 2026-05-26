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
      lib = pkgs.lib;
      latestPython = pkgs.python314;
      commonTools = with pkgs; [prek uv];
      supportedPythons = with pkgs; [
        python314
        python313
        python312
        python311
        pypy3
      ];

      mkPathPrefix = packages: ''export PATH="${lib.makeBinPath packages}:$PATH"'';

      mkUvShellHook = {
        packages,
        python ? null,
        projectEnv ? null,
        syncArgs ? null,
        activate ? false,
        extraShellHook ? "",
      }:
        lib.concatStringsSep "\n" (
          lib.filter (line: line != "") [
            (mkPathPrefix packages)
            (if projectEnv != null then ''export UV_PROJECT_ENVIRONMENT="${projectEnv}"'' else "")
            (if python != null then ''export UV_PYTHON="${python.interpreter}"'' else "")
            (if python != null then ''export UV_PYTHON_DOWNLOADS=never'' else "")
            (if syncArgs != null then "uv sync ${syncArgs}" else "")
            extraShellHook
            (if activate && projectEnv != null then ''source "$UV_PROJECT_ENVIRONMENT/bin/activate"'' else "")
          ]
        );

      mkUvShell = {
        python,
        projectEnv ? null,
        syncArgs ? null,
        activate ? false,
        extraPackages ? [],
        extraShellHook ? "",
      }:
        let
          packages = commonTools ++ [python] ++ extraPackages;
        in
        pkgs.mkShell {
          inherit packages;
          shellHook = mkUvShellHook {
            inherit packages python projectEnv syncArgs activate extraShellHook;
          };
        };

      mkTestShell = { python, projectEnv }:
        mkUvShell {
          inherit python projectEnv;
          syncArgs = "--only-group=test";
          activate = true;
          extraShellHook = ''
            uv pip install --python "$UV_PROJECT_ENVIRONMENT/bin/python" --no-deps -e .
          '';
        };
    in {
      devShells = {
        default =
          let
            packages = commonTools ++ supportedPythons;
          in
          pkgs.mkShell {
            inherit packages;
            shellHook = mkUvShellHook {
              inherit packages;
              python = latestPython;
              projectEnv = ".venv";
              activate = true;
              extraShellHook = ''
                ./init_dev_env
              '';
            };
          };
        benchmark = mkUvShell {
          python = latestPython;
          projectEnv = ".venv-benchmark";
          syncArgs = "--only-group=test";
          activate = true;
        };
        build = mkUvShell {
          python = pkgs.python313;
        };
        lint = pkgs.mkShell {
          packages = with pkgs; [prek];
          shellHook = mkPathPrefix [pkgs.prek];
        };
        test311 = mkTestShell {
          python = pkgs.python311;
          projectEnv = ".venv-test-3.11";
        };
        test312 = mkTestShell {
          python = pkgs.python312;
          projectEnv = ".venv-test-3.12";
        };
        test313 = mkTestShell {
          python = pkgs.python313;
          projectEnv = ".venv-test-3.13";
        };
        test314 = mkTestShell {
          python = pkgs.python314;
          projectEnv = ".venv-test-3.14";
        };
        testPyPy311 = mkTestShell {
          python = pkgs.pypy3;
          projectEnv = ".venv-test-pypy3.11";
        };
        update_deps = mkUvShell {
          python = latestPython;
        };
      };
    });
}
