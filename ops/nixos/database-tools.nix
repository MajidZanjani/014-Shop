# Explicit source bytes only; no bundled runtime, executable launcher or activation.
{ pkgs }:
let
  names = [ "guard.py" "control.py" "database.py" "process_probe.py"
    "schema_authorization.py" "ledger_bootstrap.py" "schema_reconciliation.py" "operator_inspect.py" "record_bundle.py" "operator_schema.py" ];
  entries = (map (name: {
    name = "libexec/shop/database/${name}";
    # Copy individual bytes, not a reference into the entire repository closure.
    path = pkgs.writeText "shop-db-${name}" (builtins.readFile (../runtime + "/${name}"));
  }) names) ++ [{
    name = "share/shop/schema-ledger.sql";
    path = pkgs.writeText "shop-schema-ledger.sql" (builtins.readFile ../postgresql/schema-ledger.sql);
  }];
  hashes = (map (name: {
    name = "libexec/shop/database/${name}";
    value = builtins.hashFile "sha256" (../runtime + "/${name}");
  }) names) ++ [{
    name = "share/shop/schema-ledger.sql";
    value = builtins.hashFile "sha256" ../postgresql/schema-ledger.sql;
  }];
  manifest = pkgs.writeText "shop-database-tools.json" (builtins.toJSON {
    schema_version = 1;
    artifact_kind = "inert-database-tools-source";
    executable = false;
    runtime_qualified = false;
    production_activation = false;
    files = builtins.listToAttrs hashes;
  });
in pkgs.linkFarm "shop-database-tools-source" (entries ++ [{
  name = "share/shop/database-tools.json"; path = manifest;
}])
