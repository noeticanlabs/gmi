# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"
  # Use https://search.nixos.org/packages to find packages.
  # We only need the base Python interpreter from Nix.
  # All other Python packages will be managed by the virtual environment.
  packages = [
    pkgs.python311
  ];
  # Sets environment variables in the workspace
  env = {
    # Custom command prompt showing project name and git branch
    PS1 = "\[\033[1;34m\]gmi\[\033[0m\] \[\033[1;32m\]\$(git branch 2>/dev/null | sed -n 's/^* //p' || echo 'main')\]:\[\033[1;36m\]\w\[\033[0m\] \$ ";
    # Disable automatic virtualenv creation, as we manage our own.
    VIRTUAL_ENV_DISABLE_PROMPT = "1";
  };
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
      "google.gemini-cli-vscode-ide-companion"
    ];
    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Create virtual environment and install both packages in editable mode.
        # NOTE: venv is REQUIRED because Nix blocks pip from modifying the system Python.
        setup-venv = ''
          python -m venv .venv
          .venv/bin/pip install --upgrade pip
          .venv/bin/pip install -e ".[dev]"
          .venv/bin/pip install -e "./gmos[dev]"
        '';
        # Open editors for the following files by default, if they exist:
        default.openFiles = [ ".idx/dev.nix" "README.md" "SETUP.md" ];
      };
      # Runs when the workspace is (re)started
      onStart = {
        # Run tests for both packages using the venv's pytest.
        # The path to pytest must be relative from within the gmos directory.
        run-tests = ".venv/bin/pytest && (cd gmos && ../.venv/bin/pytest)";
      };
    };
    previews = {
      enable = true;
      previews = {};
    };
  };
}
