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
    databaseTools = import ./database-tools.nix { inherit pkgs; };
    operatorInspection = import ./operator-runtime.nix {
      inherit pkgs python pythonEnv postgres; source = databaseTools;
    };
    operatorFailure = import ./operator-runtime.nix {
      inherit pkgs python pythonEnv postgres;
      source = pkgs.writeTextDir "libexec/shop/database/operator_inspect.py"
        "raise RuntimeError('synthetic startup detail must stay private')\n";
    };
    operatorSchema = import ./operator-runtime.nix {
      inherit pkgs python pythonEnv postgres; source = databaseTools; command = "schema";
    };
    schemaFailure = import ./operator-runtime.nix {
      inherit pkgs python pythonEnv postgres; command = "schema";
      source = pkgs.writeTextDir "libexec/shop/database/operator_schema.py"
        "raise RuntimeError('synthetic schema startup detail must stay private')\n";
    };
    # Check-only source tests exec descriptor preservation; no database imports,
    # credentials, authority records or production alternative.
    schemaFdFixture = import ./operator-runtime.nix {
      inherit pkgs python pythonEnv postgres; command = "schema";
      source = pkgs.writeTextDir "libexec/shop/database/operator_schema.py" ''
        import os
        def entrypoint():
            first=os.fstat(0); third=os.fstat(3)
            assert first.st_uid == os.geteuid() and third.st_uid == os.geteuid()
            assert first.st_mode & 0o777 == 0o600 and third.st_mode & 0o777 == 0o600
            assert os.read(0,64) == b'synthetic-artifact'
            assert os.read(3,64) == b'synthetic-credential'
            assert dict(os.environ) == {'LANG':'C','LC_ALL':'C','HOME':'/nonexistent','PSYCOPG_IMPL':'python'}
            os.write(1,b'private_fds_preserved\n')
            return 0
      '';
    };
    runtime = import ./python-runtime.nix { inherit pkgs pythonEnv postgres; };
    # Only Python source is admitted; no .env, fixtures, caches or private data.
    appSource = pkgs.lib.cleanSourceWith {
      src = ../../backend;
      filter = path: type: type == "directory" || pkgs.lib.hasSuffix ".py" path;
    };
    appTree = pkgs.runCommand "shop-python-source" {} ''
      mkdir -p $out/app
      cp -r ${appSource}/. $out/app/
    '';
    gatewayConfig = pkgs.writeTextDir "etc/shop/Caddyfile" ''
      { admin off; auto_https off }
      :8080 {
        @private_ready path /health/ready
        respond @private_ready 404
        reverse_proxy shop-app:8000
      }
    '';
    identityTree = pkgs.runCommand "shop-container-identities" {} ''
      mkdir -p $out/etc $out/app $out/tmp
      chmod 1777 $out/tmp
      echo 'shop:x:10001:10001:shop:/tmp:/sbin/nologin' > $out/etc/passwd
      echo 'shop:x:10001:' > $out/etc/group
    '';
    image = name: contents: command: pkgs.dockerTools.buildLayeredImage {
      inherit name; contents = contents ++ [ identityTree ];
      tag = "candidate"; created = "1970-01-01T00:00:01Z";
      config = { User = "10001:10001"; WorkingDir = "/app"; Cmd = command;
        Env = [ "PYTHONDONTWRITEBYTECODE=1" "PYTHONNOUSERSITE=1" ]; };
    };
    appImage = image "shop-app" [ runtime appTree ] [ "${runtime}/bin/python" "-m" "gunicorn" "shop.wsgi:application" "--bind" "0.0.0.0:8000" "--workers" "2" "--threads" "1" "--timeout" "30" ];
    workerImage = image "shop-worker" [ runtime appTree ] [ "${runtime}/bin/python" "/app/manage.py" "run_worker" "--poll-interval" "1" "--lease-seconds" "30" "--max-attempts" "3" ];
    postgresDiagnostics = pkgs.writeTextDir "libexec/shop/postgres_entrypoint.py" (builtins.readFile ../runtime/postgres_entrypoint.py);
    postgresCommand = [ "${python}/bin/python3" "-I" "${postgresDiagnostics}/libexec/shop/postgres_entrypoint.py" "${postgres}/bin/postgres" "-D" "/var/lib/shop/postgres" "-c" "fsync=on" "-c" "synchronous_commit=on" "-c" "full_page_writes=on" "-c" "config_file=/var/lib/shop/config/postgresql.conf" ];
    # PGDATA must already exist and be attested; no implicit initdb entrypoint.
    postgresImage = image "shop-postgres" [ postgres python postgresDiagnostics ] postgresCommand;
    gatewayImage = image "shop-gateway" [ pkgs.caddy gatewayConfig ] [ "${pkgs.caddy}/bin/caddy" "run" "--config" "/etc/shop/Caddyfile" "--adapter" "caddyfile" ];
  in {
    nixosModules.shop = import ./modules/shop.nix;
    packages.${system} = { shop-app = appImage; shop-worker = workerImage;
      shop-postgres = postgresImage; shop-gateway = gatewayImage; shop-python-runtime = runtime; shop-database-tools-source = databaseTools; shop-operator-inspect = operatorInspection.launcher; shop-operator-schema = operatorSchema.launcher; };
    checks.${system} = {
      operator-startup-denial = operatorFailure.launcher;
      schema-startup-denial = schemaFailure.launcher;
      schema-private-fds = schemaFdFixture.launcher;
    };
    deploymentMetadata.${system} = {
      status = "candidate; compatibility/build/OCI digests/off-host qualification pending";
      imageDerivations = map (x: x.drvPath) [ appImage workerImage postgresImage gatewayImage ];
      runtimeVersion = pkgs.podman.version;
      systemdVersion = pkgs.systemd.version;
      postgresDiagnostics = { command = postgresCommand; workerSource = "${postgresDiagnostics}/libexec/shop/postgres_entrypoint.py"; nativePidContract = "execve; rootless lifecycle pending"; runtimeQualified = false; };
      operatorInspection = operatorInspection.metadata;
      operatorSchema = operatorSchema.metadata;
      databaseTools = { source = toString databaseTools; manifest = "${databaseTools}/share/shop/database-tools.json"; executable = false; runtimeQualified = false; productionActivation = false; };
      productionActivation = false;
    };
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
