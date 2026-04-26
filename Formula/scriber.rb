class Scriber < Formula
  desc "Offline transcription for qualitative researchers"
  homepage "https://github.com/stvbao/scriber"
  version "0.1.0"

  # Apple Silicon CLI bundle produced by .github/workflows/release.yml.
  # To update: run `shasum -a 256 scriber-<ver>-macos-arm64.tar.gz` on the
  # release artifact and paste it below.
  url "https://github.com/stvbao/scriber/releases/download/v#{version}/scriber-#{version}-macos-arm64.tar.gz"
  sha256 "REPLACE_WITH_SHA256_FROM_RELEASE"

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
