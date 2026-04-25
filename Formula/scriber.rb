class Scriber < Formula
  desc "Offline transcription for qualitative researchers"
  homepage "https://github.com/stvbao/scriber"
  version "0.1.0"

  # To update: run `shasum -a 256 scriber-<ver>-macos-arm64.tar.gz` on the
  # artifact produced by the release workflow and paste it below.
  on_macos do
    on_arm do
      url "https://github.com/stvbao/scriber/releases/download/v#{version}/scriber-#{version}-macos-arm64.tar.gz"
      sha256 "REPLACE_WITH_SHA256_FROM_RELEASE"
    end

    # Intel Mac: build from source (no pre-built binary yet).
    # Run: brew install stvbao/scriber/scriber --build-from-source
    on_intel do
      url "https://github.com/stvbao/scriber/archive/refs/tags/v#{version}.tar.gz"
      sha256 "REPLACE_WITH_SOURCE_SHA256"

      depends_on "python@3.12"
      depends_on "uv" => :build

      def install
        system "uv", "sync"
        system ".venv/bin/pyinstaller", "scriber-mac.spec", "--noconfirm"
        bin.install "dist/Scriber.app/Contents/MacOS/scriber"
      end
    end
  end

  # ── Pre-built binary install (arm64) ────────────────────────────────────────
  def install
    bin.install "scriber"
  end

  test do
    # Smoke-test: --help should exit 0 and print usage
    assert_match "scriber", shell_output("#{bin}/scriber --help 2>&1", 0)
  end
end
