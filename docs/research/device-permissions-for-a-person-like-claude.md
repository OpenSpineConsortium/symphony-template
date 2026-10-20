# Device permissions for talking with Claude like a person

Source: the thread "Outlook digest with one-touch decisions", 2026-10-20, on the owner's question of what other permissions Symphony might ever need to be native on CentOS, Ubuntu, iOS, macOS, Windows and Android: camera, microphone, fingerprint, VR, Bluetooth, and one day a virtual avatar as the agent, answering like a person and reading facial expressions and intonation. Nothing here is built. The platform permission names below are the author's knowledge of each platform's documentation, not read again this session except where a link is given; check each against the platform's own pages when the feature is built. docs/research/native-ios-app.md is the earlier note on a native iOS app.

## The short answer

None of these is a Microsoft 365 permission, so none goes to Wayne State C&IT. Camera, microphone, fingerprint, Bluetooth and VR are granted by the person on each device, at the moment the app first asks, by the operating system or the browser; an IT department only enters where it manages the device (a university laptop or phone under Intune can turn the camera or Bluetooth off). The Graph request stays what docs/research/microsoft-365-permissions.md says.

## What each power needs, per platform

| Power | Web (the control panel in a browser) | iOS and iPadOS | Android | macOS | Windows | Linux (Ubuntu, CentOS) |
|---|---|---|---|---|---|---|
| Camera | getUserMedia, asked per site | NSCameraUsageDescription | CAMERA | camera (TCC prompt) | webcam capability, Settings privacy | none; Flatpak or Snap portal where sandboxed |
| Microphone | getUserMedia | NSMicrophoneUsageDescription; NSSpeechRecognitionUsageDescription for Apple's speech recognizer | RECORD_AUDIO; FOREGROUND_SERVICE_MICROPHONE to listen in the background | microphone (TCC) | microphone capability | PipeWire or PulseAudio, portal where sandboxed |
| Fingerprint or face to unlock | WebAuthn passkeys; the site never sees the fingerprint | NSFaceIDUsageDescription; LocalAuthentication | USE_BIOMETRIC | LocalAuthentication (Touch ID) | Windows Hello | fprintd through PAM; no browser passkey on most distributions beyond a security key |
| Bluetooth (headsets, sensors) | Web Bluetooth in Chrome and Edge only; Safari and every iOS browser have none | NSBluetoothAlwaysUsageDescription | BLUETOOTH_CONNECT, BLUETOOTH_SCAN | Bluetooth (TCC) | bluetooth capability | BlueZ over D-Bus |
| VR or AR | WebXR in Chrome-based browsers, Quest's browser and Safari on Vision Pro; not on iOS | ARKit (camera permission) | ARCore (camera permission) | none native | WebXR or OpenXR | OpenXR (Monado) |
| Notifications | Push API with the person's consent | push entitlement and the person's yes | POST_NOTIFICATIONS | notifications prompt | toast notifications | desktop notifications, no prompt |
| Screen sharing | getDisplayMedia, per session | ReplayKit broadcast | MediaProjection, per session | Screen Recording (TCC) | Graphics Capture picker | PipeWire screencast portal |

Sources for the two web rows that are easiest to get wrong: Safari on iOS has no Web Bluetooth, only a third-party Safari extension that adds its own API ([WebBLE on the App Store](https://apps.apple.com/de/app/ioswebble/id6761301368)), and WebXR is in Safari on Vision Pro but not on iOS ([Apple developer forums](https://developer.apple.com/forums/thread/733772)).

Two consequences for Symphony. A web page gets camera, microphone, passkeys and WebXR on every platform but iOS's Bluetooth and VR, so the control panel can go a long way before a native app is needed. And iOS is where a native app first earns its keep, for Bluetooth and background listening, which docs/research/native-ios-app.md weighs.

## The avatar that reads faces and voice

The talking part is ordinary: a microphone, speech to text, Claude, text to speech, and a drawn or rendered face, with the camera only if the person wants to be seen. Claude's own apps already offer voice conversation; what an avatar adds is the face.

Reading the person's emotions from face and voice is where the limits are, and they are not permissions:

- The EU AI Act forbids AI that infers emotions from biometric data in workplaces and education, from 2 February 2025, with exceptions for medical or safety reasons ([Article 5(1)(f) summary](https://myctrl.tools/frameworks/eu-ai-act/art-5-1-f); [Lewis Silkin](https://www.lewissilkin.com/en/insights/2025/02/17/understanding-the-eu-ai-acts-prohibited-practices-key-workplace-and-advertising-102k011)). The Commission's guidelines of 4 February 2025 count facial expressions and typing among the signals. A university is an education institution, so a feature like this would be off for any European collaborator or student, and its use at Wayne State is a question for the university's counsel and the IRB, not for the code (inferred; US law has no such ban, though Illinois's BIPA and similar state laws govern face and voice data).
- Microsoft retired the emotion attributes of Azure Face in 2022, with existing customers cut off on 30 June 2023, citing the lack of scientific consensus on what an emotion is ([Azure update](https://azure.microsoft.com/en-in/updates/facelimitedaccess/)). Any emotion reading Symphony offered would rest on models whose validity the largest vendor itself declined to stand behind.

What can be done without those limits: the avatar responding to what the person says and how they say it in words (pace, a pause, "I'm tired"), the person telling it their mood, and tone of voice used only to time a reply, not to label an emotion; and everything camera- or voice-derived processed on the device and never stored, so no face or voice data leaves it.

## What waits on the owner

- Whether the first native step is iOS (docs/research/native-ios-app.md) or the web panel's voice, which needs only the microphone in the browser.
- Whether emotion reading is wanted at all, given the two limits above; if so, a question for Wayne State's counsel and the IRB before any code.
