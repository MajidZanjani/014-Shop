{
  description = "SLL shop native development tools; no host deployment";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    # Reviewed source bytes, not an assertion of a successful native build.
    nodeSource = pkgs.nodejs-slim_24.overrideAttrs (_: {
      version = "24.22.0";
      src = pkgs.fetchurl {
        url = "https://nodejs.org/dist/v24.22.0/node-v24.22.0.tar.xz";
        sha256 = "41f97cff2c666f1f8293dc5f85c65e8dd605c16b43fd9febd49ede32ee1e0329";
      };
    });
    node = pkgs.nodejs_24.override { nodejs-slim = nodeSource; };
    python = pkgs.python313.override {
      self = python;
      # This shell is native-only. The pinned recipe filters attrsets from its
      # splice overrides, otherwise forwarding the new hash with the old sourceVersion.
      __splices = {
        pythonOnBuildForBuild = python;
        pythonOnBuildForHost = python;
        pythonOnBuildForTarget = python;
        pythonOnHostForHost = python;
        pythonOnTargetForTarget = python;
      };
      sourceVersion = { major = "3"; minor = "13"; patch = "16"; suffix = ""; };
      hash = "sha256:f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d";
    };
    pip = python.pkgs.buildPythonPackage {
      pname = "pip";
      version = "26.2.1";
      format = "wheel";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/f3/6e/1736e5b4ae2b778ef2f81c47d797de9f891d4d8acb047a24ca37a60294dd/pip-26.2.1-py3-none-any.whl";
        sha256 = "71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e";
      };
      pythonImportsCheck = [ "pip" ];
    };
    pythonEnv = python.withPackages (_: [ pip ]);
    postgres = pkgs.postgresql_18.overrideAttrs (_: {
      src = pkgs.fetchurl {
        url = "https://ftp.postgresql.org/pub/source/v18.6/postgresql-18.6.tar.bz2";
        sha256 = "555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f";
      };
    });
  in {
    devShells.${system}.default = pkgs.mkShell {
      PYTHONDONTWRITEBYTECODE = "1";
      PYTHONNOUSERSITE = "1";
      packages = [ node pythonEnv postgres
        pkgs.systemd pkgs.util-linux pkgs.git pkgs.curl pkgs.gnutar pkgs.xz pkgs.bzip2
        pkgs.gzip pkgs.unzip pkgs.gnumake pkgs.gcc pkgs.pkg-config ];
      SHOP_TOOL_PATH = pkgs.lib.makeBinPath [ node pythonEnv postgres ];
      SHOP_PYTHON = "${pythonEnv}/bin/python3";
      SHOP_NODE = "${node}/bin/node";
      SHOP_NPM = "${node}/bin/npm";
      SHOP_POSTGRES_BIN = "${postgres}/bin";
    };
  };
}
