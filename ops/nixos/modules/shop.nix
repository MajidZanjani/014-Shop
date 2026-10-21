{ config, lib, pkgs, ... }:
let
  cfg = config.services.xspiShop;
  uid = if cfg.uid == null then 0 else cfg.uid;
  guard = pkgs.writeShellScript "shop-storage-guard" ''
    exec ${pkgs.python3}/bin/python3 ${../../runtime/guard.py} --zfs ${pkgs.zfs}/bin/zfs --pg-control ${pkgs.postgresql_18}/bin/pg_controldata "$@"
  '';
  render = service: lib.replaceStrings
    [ "@APP_IMAGE@" "@WORKER_IMAGE@" "@POSTGRES_IMAGE@" "@GATEWAY_IMAGE@" "@GUARD@" ]
    [ cfg.images.app cfg.images.worker cfg.images.postgres cfg.images.gateway (toString guard) ]
    (builtins.readFile (../../quadlet + "/shop-${service}.container"));
in {
  options.services.xspiShop = {
    enable = lib.mkEnableOption "new isolated rootless shop (never implies host authorization)";
    uid = lib.mkOption { type = lib.types.nullOr lib.types.ints.positive; default = null; };
    gid = lib.mkOption { type = lib.types.nullOr lib.types.ints.positive; default = null; };
    subordinateStart = lib.mkOption { type = lib.types.nullOr lib.types.ints.positive; default = null; };
    qualifiedInventoryAndActivation = lib.mkOption { type = lib.types.bool; default = false; description = "Operator attests actual full reviewed inventory/activation impact; never inferred."; };
    images = lib.genAttrs [ "app" "worker" "postgres" "gateway" ] (_: lib.mkOption { type = lib.types.str; default = "UNQUALIFIED"; });
  };
  config = lib.mkIf cfg.enable {
    assertions = [
      { assertion = cfg.qualifiedInventoryAndActivation && cfg.uid != null && cfg.gid != null && cfg.subordinateStart != null;
        message = "Shop requires actual reviewed inventory/activation, unused UID/GID/subordinate ranges and owned storage; no proposed default IDs."; }
      { assertion = lib.all (image: builtins.match "localhost/shop-[a-z]+@sha256:[0-9a-f]{64}" image != null) (lib.attrValues cfg.images);
        message = "Shop images require actual reviewed local immutable manifest digests; candidate tags forbidden."; }
      { assertion = lib.all (u: u.name == "shopsvc" || u.uid != cfg.uid) (lib.attrValues config.users.users);
        message = "Shop UID overlaps another declared owner."; }
      { assertion = cfg.gid != null && lib.all (g: g.name == "shopsvc" || g.gid != cfg.gid) (lib.attrValues config.users.groups);
        message = "Shop GID overlaps another declared group."; }
      { assertion = cfg.subordinateStart != null && lib.all (u: u.name == "shopsvc" ||
          (lib.all (r: cfg.subordinateStart + 65536 <= r.startUid || r.startUid + r.count <= cfg.subordinateStart) u.subUidRanges &&
           lib.all (r: cfg.subordinateStart + 65536 <= r.startGid || r.startGid + r.count <= cfg.subordinateStart) u.subGidRanges)) (lib.attrValues config.users.users);
        message = "Shop subordinate IDs overlap another declared owner."; }
    ];
    users.groups.shopsvc.gid = cfg.gid;
    users.users.shopsvc = {
      isSystemUser = true; inherit (cfg) uid; group = "shopsvc";
      home = "/srv/shop"; createHome = false;
      subUidRanges = [ { startUid = cfg.subordinateStart; count = 65536; } ];
      subGidRanges = [ { startGid = cfg.subordinateStart; count = 65536; } ];
      # Do not invoke NixOS's all-user linger management.
    };
    systemd.slices."user-${toString uid}" = {
      description = "New shop account aggregate; all descendants including runtime helpers/backups";
      sliceConfig = { CPUQuota = "200%"; MemoryHigh = "6G"; MemoryMax = "8G"; TasksMax = 1024; };
    };
    systemd.services.shop-linger = {
      description = "Linger only the newly qualified shopsvc account";
      wantedBy = [ "multi-user.target" ];
      serviceConfig = { Type = "oneshot"; RemainAfterExit = true;
        ExecStart = "${pkgs.systemd}/bin/loginctl enable-linger shopsvc"; };
    };
    environment.etc = (lib.listToAttrs (map (service: {
      name = "containers/systemd/users/${toString uid}/shop-${service}.container";
      value.text = render service;
    }) [ "app" "worker" "postgres" "gateway" ])) // {
      "containers/systemd/users/${toString uid}/shop-private.network".source = ../../quadlet/shop-private.network;
    };
    # No global Podman/firewall/mount/pool/journal/subuid-helper activation.
    # Storage/runtime user configuration and mount identity are required by guard;
    # absent or unsupported prerequisites fail closed, never auto-repair the host.
  };
}
