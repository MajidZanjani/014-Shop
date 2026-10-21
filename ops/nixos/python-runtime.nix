{ pkgs, pythonEnv, postgres }:
let
  wheels = builtins.fromJSON (builtins.readFile ../runtime/wheels.json);
  files = map (w: pkgs.fetchurl { name = w.filename; inherit (w) url sha256; }) wheels;
  wheelhouse = pkgs.linkFarm "shop-reviewed-runtime-wheels" (pkgs.lib.zipListsWith
    (w: path: { name = w.filename; inherit path; }) wheels files);
in pkgs.runCommand "shop-python-runtime" { nativeBuildInputs = [ pythonEnv ]; } ''
  export HOME=$TMPDIR PIP_CONFIG_FILE=/dev/null PYTHONNOUSERSITE=1
  mkdir -p "$out/site" "$out/bin"
  ${pythonEnv}/bin/python3 -I -m pip install --no-index --only-binary=:all: \
    --require-hashes --no-compile --find-links=${wheelhouse} \
    --target="$out/site" -r ${../../backend/requirements/runtime-linux-py313.txt}
  cat > "$out/bin/python" <<EOF
  #!${pkgs.runtimeShell}
  export PYTHONPATH=$out/site:/app
  export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [ postgres.lib ]}
  export PSYCOPG_IMPL=python PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
  exec ${pythonEnv}/bin/python3 "\$@"
  EOF
  chmod 0555 "$out/bin/python"
''
