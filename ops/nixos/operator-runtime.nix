# Standalone candidate launcher only; no NixOS installation or host activation.
{ pkgs, python, pythonEnv, postgres, source, command ? "inspect" }:
let
  inspection = command == "inspect";
  executable = if inspection then "shop-operator-inspect" else "shop-operator-schema";
  module = if inspection then "operator_inspect" else "operator_schema";
  errorEvent = if inspection then "operator.inspection_denied" else "operator.schema_outcome_unconfirmed";
  selected = builtins.filter (w: w.name == "psycopg")
    (builtins.fromJSON (builtins.readFile ../runtime/wheels.json));
  wheel = builtins.head selected;
  approvedHash = "a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631";
  archive = pkgs.fetchurl { name = wheel.filename; inherit (wheel) url sha256; };
  wheelhouse = pkgs.linkFarm "shop-operator-wheelhouse" [{ name = wheel.filename; path = archive; }];
  requirement = pkgs.writeText "shop-operator-requirement.txt"
    "psycopg==3.3.6 --hash=sha256:${approvedHash}\n";
  site = pkgs.runCommand "shop-operator-psycopg-site" { nativeBuildInputs = [ pythonEnv ]; } ''
    export HOME=$TMPDIR PIP_CONFIG_FILE=/dev/null PYTHONNOUSERSITE=1
    mkdir -p $out/site
    ${pythonEnv}/bin/python3 -I -m pip install --no-index --no-deps --no-compile \
      --only-binary=:all: --require-hashes --find-links=${wheelhouse} \
      --target=$out/site -r ${requirement}
  '';
  libpq = "${postgres.lib}/lib/libpq.so.5";
  libc = "${pkgs.stdenv.cc.libc}/lib/libc.so.6";
  driver = pkgs.writeText "${executable}-driver.py" ''
    import os,sys
    sys.dont_write_bytecode=True
    status=1
    try:
        if not (sys.flags.isolated == 1 and sys.version_info[:3] == (3,13,16) and sys.platform == 'linux'):
            raise RuntimeError()
        os.environ.clear()
        os.environ.update({'LANG':'C','LC_ALL':'C','HOME':'/nonexistent','PSYCOPG_IMPL':'python'})
        sys.path.insert(0,'${site}/site')
        import ctypes.util
        original=ctypes.util.find_library
        def pinned_library(name):
            if name == 'pq':
                return '${libpq}'
            if name == 'c':
                return '${libc}'
            raise RuntimeError()
        ctypes.util.find_library=pinned_library
        try:
            import psycopg
        finally:
            ctypes.util.find_library=original
        if not (psycopg.pq.__impl__ == 'python' and psycopg.pq.version() == 180006):
            raise RuntimeError()
        import importlib.metadata
        distributions=[(d.metadata['Name'].lower(),d.version) for d in importlib.metadata.distributions()]
        if distributions != [('psycopg','3.3.6')]:
            raise RuntimeError()
        sys.path.insert(0,'${source}/libexec/shop/database')
        import ${module} as command_module
        status=command_module.entrypoint()
    except BaseException:
        try:
            os.write(2,b'{"event":"${errorEvent}"}\n')
        except OSError:
            pass
    raise SystemExit(status)
  '';
  launcher = pkgs.writeShellScriptBin executable ''
    exec ${pkgs.coreutils}/bin/env -i LANG=C LC_ALL=C HOME=/nonexistent \
      ${python}/bin/python3 -I ${driver} "$@"
  '';
in assert builtins.elem command [ "inspect" "schema" ];
assert builtins.length selected == 1 && wheel.version == "3.3.6" && wheel.sha256 == approvedHash;
{
  inherit site driver launcher;
  metadata = {
    package = toString launcher;
    executable = "${launcher}/bin/${executable}";
    driver = toString driver;
    source = toString source;
    runtimeSite = "${site}/site";
    python = "${python}/bin/python3";
    inherit libpq libc;
    pythonVersion = "3.13.16";
    psycopgVersion = "3.3.6";
    libpqVersion = 180006;
    readOnly = inspection;
    installed = false;
    runtimeQualified = false;
    productionActivation = false;
  };
}
