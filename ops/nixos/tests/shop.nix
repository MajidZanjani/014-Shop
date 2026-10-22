# Pure candidate-contract fixture, not a runtime proof.  The lifecycle driver
# remains blocked until exact images, bootstrap wrapper and runner are ready.
{ nixpkgs, shopModule }:
let
  host = extra: nixpkgs.lib.nixosSystem {
    system = "x86_64-linux";
    modules = [ shopModule {
      system.stateVersion = "26.05";
      # Protected pre-existing synthetic owner and manager drop-in sentinel.
      users.groups.fixture-existing.gid = 9908;
      users.users.fixture-existing = { isSystemUser = true; uid = 9908; group = "fixture-existing"; home = "/var/empty"; };
      environment.etc."systemd/system/user@9908.service.d/10-existing.conf".text = "[Service]\nEnvironment=EXISTING_FIXTURE=preserved\n";
      boot.loader.grub.enable = false;
      fileSystems."/" = { device = "none"; fsType = "tmpfs"; };
    } extra ];
  };
  disabled = host {};
  runtime = import ../rootless-runtime.nix {
    pkgs = import nixpkgs { system = "x86_64-linux"; };
    uid = 9909;
    guard = "/nix/store/00000000000000000000000000000000-synthetic-guard";
  };
  candidate = host { services.xspiShop = {
    enable = true;
    uid = 9909; gid = 9909; subordinateStart = 900000;
    qualifiedInventoryAndActivation = true; # Synthetic evaluated VM config only.
    images = builtins.listToAttrs (map (name: {
      inherit name; value = "localhost/shop-${name}@sha256:${builtins.concatStringsSep "" (builtins.genList (_: "0") 64)}";
    }) [ "app" "worker" "postgres" "gateway" ]);
  }; };
in {
  disabled = {
    accountAbsent = !(builtins.hasAttr "shopsvc" disabled.config.users.users);
    lingerAbsent = !(builtins.hasAttr "shop-linger" disabled.config.systemd.services);
    globalPodmanDisabled = !disabled.config.virtualisation.podman.enable;
    databaseConfigAbsent = !(builtins.hasAttr "xspi-shop/postgresql.conf" disabled.config.environment.etc);
    bootstrapAbsent = !(builtins.hasAttr "xspi-shop/bootstrap" disabled.config.environment.etc);
    managerDropinAbsent = !(builtins.hasAttr "systemd/system/user@9909.service.d/50-shop-generators.conf" disabled.config.environment.etc);
    runtimeArtifactsAbsent = !(builtins.hasAttr "xspi-shop/runtime/podman" disabled.config.environment.etc);
  };
  runtimeCandidate = {
    inherit (runtime) containersText storageText environment podmanText generatorText unitDir managerDropinPath managerDropinText;
    generatorBundle = toString runtime.generatorBundle;
    artifacts = builtins.attrNames runtime.etc;
    productionActivation = false;
  };
  syntheticCandidate = {
    assertions = map (x: { inherit (x) assertion; message = if x.assertion then "passed" else x.message; }) candidate.config.assertions;
    bounds = candidate.config.systemd.slices."user-9909".sliceConfig;
    units = builtins.attrNames candidate.config.environment.etc;
    automaticGlobalLingerUnchanged = candidate.config.users.manageLingering == disabled.config.users.manageLingering;
    shopLingerUnmanagedByGlobalService = candidate.config.users.users.shopsvc.linger == null;
    existingManagerConfigUnchanged = candidate.config.environment.etc."systemd/system/user@9908.service.d/10-existing.conf".text == disabled.config.environment.etc."systemd/system/user@9908.service.d/10-existing.conf".text;
    existingAccountUnchanged = candidate.config.users.users.fixture-existing.uid == disabled.config.users.users.fixture-existing.uid && candidate.config.users.users.fixture-existing.subUidRanges == disabled.config.users.users.fixture-existing.subUidRanges && candidate.config.users.users.fixture-existing.subGidRanges == disabled.config.users.users.fixture-existing.subGidRanges;
    globalUserGeneratorsUnchanged = candidate.config.systemd.user.generators == disabled.config.systemd.user.generators;
    managerGeneratorBundle = toString candidate.config.environment.etc."xspi-shop/runtime/user-generators".source;
    managerDropinText = candidate.config.environment.etc."systemd/system/user@9909.service.d/50-shop-generators.conf".text;
    managerDropinPaths = builtins.filter (path: nixpkgs.lib.hasPrefix "systemd/system/user@" path && nixpkgs.lib.hasSuffix "/50-shop-generators.conf" path) (builtins.attrNames candidate.config.environment.etc);
    disabledManagerDropinPaths = builtins.filter (path: nixpkgs.lib.hasSuffix "/50-shop-generators.conf" path) (builtins.attrNames disabled.config.environment.etc);
    databaseConfig = builtins.readFile candidate.config.environment.etc."xspi-shop/postgresql.conf".source;
    databaseHba = builtins.readFile candidate.config.environment.etc."xspi-shop/pg_hba.conf".source;
    bootstrapArtifact = toString candidate.config.environment.etc."xspi-shop/bootstrap".source;
    bootstrapScript = candidate.config.environment.etc."xspi-shop/bootstrap".source.text;
    activationAuthorized = false;
    evidence = "synthetic evaluation; zero digests are fixture data, never deployable artifacts";
  };
}
