# Candidate account-scoped runtime artifacts. Evaluation never installs them.
{ pkgs, uid, guard }:
assert builtins.isInt uid && uid > 0;
let
  lib = pkgs.lib;
  runtimeDir = "/run/user/${toString uid}";
  unitDir = "/etc/containers/systemd/users/${toString uid}";
  containersText = ''
    [containers]
    log_driver = "k8s-file"
    log_size_max = 10485760
    [engine]
    cgroup_manager = "systemd"
    events_logger = "none"
    runtime = "crun"
    conmon_path = ["${pkgs.conmon}/bin/conmon"]
    helper_binaries_dir = ["${pkgs.podman}/libexec/podman"]
    tmp_dir = "/srv/shop/tmp/libpod"
    volume_path = "/srv/shop/volumes"
    pull_policy = "never"
    [engine.runtimes]
    crun = ["${pkgs.crun}/bin/crun"]
    [network]
    network_backend = "netavark"
    network_config_dir = "/srv/shop/containers/networks"
    default_rootless_network_cmd = "pasta"
  '';
  storageText = ''
    [storage]
    driver = "overlay"
    runroot = "${runtimeDir}/shop-containers"
    graphroot = "/srv/shop/containers/storage"
    rootless_storage_path = "/srv/shop/containers/storage"
    [storage.options.overlay]
    mount_program = "${pkgs.fuse-overlayfs}/bin/fuse-overlayfs"
  '';
  containers = pkgs.writeText "shop-containers.conf" containersText;
  storage = pkgs.writeText "shop-storage.conf" storageText;
  registries = pkgs.writeText "shop-registries.conf" ''
    unqualified-search-registries = []
    short-name-mode = "enforcing"
  '';
  environment = {
    HOME = "/srv/shop";
    XDG_RUNTIME_DIR = runtimeDir;
    XDG_CONFIG_HOME = "/srv/shop/control/runtime";
    XDG_DATA_HOME = "/srv/shop/containers";
    TMPDIR = "/srv/shop/tmp";
    CONTAINERS_CONF = toString containers;
    CONTAINERS_STORAGE_CONF = toString storage;
    CONTAINERS_REGISTRIES_CONF = toString registries;
    DBUS_SESSION_BUS_ADDRESS = "unix:path=${runtimeDir}/bus";
    # Existing privileged namespace helpers must be qualified, never installed here.
    PATH = "${pkgs.coreutils}/bin:/run/wrappers/bin:${pkgs.podman}/libexec/podman";
    LANG = "C";
  };
  assignments = lib.concatStringsSep " \\\n      " (lib.mapAttrsToList (name: value: lib.escapeShellArg "${name}=${value}") environment);
  preflight = ''
    set -eu
    [ "$(${pkgs.coreutils}/bin/id -u)" = "${toString uid}" ] || exit 1
    [ -d '${runtimeDir}' ] && [ ! -L '${runtimeDir}' ] || exit 1
    [ "$(${pkgs.coreutils}/bin/stat -c %u '${runtimeDir}')" = "${toString uid}" ] || exit 1
    [ "$(${pkgs.coreutils}/bin/stat -c %a '${runtimeDir}')" = "700" ] || exit 1
  '';
  podmanText = ''
    ${preflight}
    ${pkgs.coreutils}/bin/env -i ${assignments} \
      ${guard} --expected /srv/shop/control/expected.json
    for dir in /srv/shop/tmp/libpod /srv/shop/volumes /srv/shop/containers/networks; do
      [ -d "$dir" ] && [ ! -L "$dir" ] || exit 1
      [ "$(${pkgs.coreutils}/bin/readlink -f "$dir")" = "$dir" ] || exit 1
      [ "$(${pkgs.coreutils}/bin/stat -c %u "$dir")" = "${toString uid}" ] || exit 1
    done
    exec ${pkgs.coreutils}/bin/env -i ${assignments} \
      "NOTIFY_SOCKET=''${NOTIFY_SOCKET-}" "PODMAN_SYSTEMD_UNIT=''${PODMAN_SYSTEMD_UNIT-}" \
      ${pkgs.podman}/bin/podman "$@"
  '';
  podman = pkgs.writeShellScript "shop-podman" podmanText;
  generatorText = ''
    ${preflight}
    exec ${pkgs.coreutils}/bin/env -i ${assignments} \
      'PODMAN=${podman}' 'QUADLET_UNIT_DIRS=${unitDir}' \
      ${pkgs.podman}/libexec/podman/quadlet --user --no-kmsg-log "$@"
  '';
  generator = pkgs.writeShellScript "shop-podman-user-generator" generatorText;
in {
  inherit containersText storageText environment podmanText generatorText podman generator;
  inherit unitDir;
  # Only root-owned documentation/artifact links; per-user discovery installation
  # and activation are a separately reviewed bootstrap operation.
  etc = {
    "xspi-shop/runtime/containers.conf".source = containers;
    "xspi-shop/runtime/storage.conf".source = storage;
    "xspi-shop/runtime/podman".source = podman;
    "xspi-shop/runtime/podman-user-generator".source = generator;
  };
}
