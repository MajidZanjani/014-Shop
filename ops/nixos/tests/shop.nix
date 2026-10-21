# Pure candidate-contract fixture, not a runtime proof.  The lifecycle driver
# remains blocked until exact images, bootstrap wrapper and runner are ready.
{ nixpkgs, shopModule }:
let
  host = extra: nixpkgs.lib.nixosSystem {
    system = "x86_64-linux";
    modules = [ shopModule {
      system.stateVersion = "26.05";
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
    runtimeArtifactsAbsent = !(builtins.hasAttr "xspi-shop/runtime/podman" disabled.config.environment.etc);
  };
  runtimeCandidate = {
    inherit (runtime) containersText storageText environment podmanText generatorText unitDir;
    artifacts = builtins.attrNames runtime.etc;
    productionActivation = false;
  };
  syntheticCandidate = {
    assertions = map (x: { inherit (x) assertion; message = if x.assertion then "passed" else x.message; }) candidate.config.assertions;
    bounds = candidate.config.systemd.slices."user-9909".sliceConfig;
    units = builtins.attrNames candidate.config.environment.etc;
    automaticGlobalLingerUnchanged = candidate.config.users.manageLingering == disabled.config.users.manageLingering;
    shopLingerUnmanagedByGlobalService = candidate.config.users.users.shopsvc.linger == null;
    globalUserGeneratorsUnchanged = candidate.config.systemd.user.generators == disabled.config.systemd.user.generators;
    activationAuthorized = false;
    evidence = "synthetic evaluation; zero digests are fixture data, never deployable artifacts";
  };
}
