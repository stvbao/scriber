class Scriber < Formula
  desc "Offline transcription for qualitative researchers"
  homepage "https://github.com/stvbao/Scriber"
  version "0.1.4"

  # Apple Silicon CLI bundle produced by .github/workflows/release.yml.
  # To update: run `shasum -a 256 scriber-<ver>-macos-arm64.tar.gz` on the
  # release artifact and paste it below.
  url "https://github.com/stvbao/Scriber/releases/download/v#{version}/scriber-#{version}-macos-arm64.tar.gz"
  sha256 "6405f14c178481dbf45aaf2807961c4b5a278028437e8ff78c5394efda742d93"

  depends_on arch: :arm64

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"scriber"
  end

  def caveats
    <<~EOS
      Scriber CLI is installed as `scriber`.
      `scriber app` launches the GUI from the CLI process; a native Dock name/icon
      requires a separate Scriber.app bundle.
    EOS
  end

  test do
    assert_match "scriber", shell_output("#{bin}/scriber --help 2>&1", 0)
    assert_match "scriber", shell_output("#{bin}/scriber cache path 2>&1", 0)
  end
end
