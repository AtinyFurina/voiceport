cask "voiceport" do
  version "0.1.1"
  sha256 "9305d1ebe5f1518fb1b5277da48045405bb0d992a6aad122135d1a6a19c2a27a"

  url "https://github.com/AtinyFurina/voiceport/releases/download/v#{version}/VoicePort.dmg"
  name "VoicePort"
  desc "语音输入前端，配合 FoloToy AI Passport 硬件"
  homepage "https://github.com/AtinyFurina/voiceport"

  app "VoicePort.app"

  zap trash: [
    "~/.passport",
  ]
end
