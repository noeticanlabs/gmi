# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"
  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.numpy
  ];
  # Sets environment variables in the workspace
  env = {
    # Custom command prompt showing project name and git branch
    PS1 = "\\[\\033[1;34m\\]gmi\\[\\033[0m\\] \\[\\033[1;32m\\]\\$(git branch 2>/dev/null | sed -n 's/^* //p' || echo 'main')\\]:\\[\\033[1;36m\\]\\w\\[\\033[0m\\] \\$ ";
    # Disable automatic virtualenv creation
    VIRTUAL_ENV_DISABLE_PROMPT = "1";
  };
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
      "google.gemini-cli-vscode-ide-companion"
    ];
    # Enable previews
    previews = {
      enable = true;
      previews = {};
    };
    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        install-deps = "pip install -e .[dev]";
        # Open editors for the following files by default, if they exist:
        default.openFiles = [ ".idx/dev.nix" "README.md" "thermo_cognition.py" ];
      };
      # Runs when the workspace is (re)started
      onStart = {
        # Example: start a background task to watch and re-build backend code
        # watch-backend = "npm run watch-backend";
      };
    };
  };
}
