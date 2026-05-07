# Prompts cookbook

Examples of how to invoke these skills effectively, organized by goal. Use this two ways:

1. **Onboarding** — copy the prompts that match what you're building
2. **Trigger validation** — if a prompt below doesn't fire the listed skill in a fresh Claude Code session, the skill's `description` frontmatter needs more specific keywords

Each entry has: the **prompt**, the **skills it should trigger**, and what **good output** looks like.

---

## 🆕 Starting a new Pexip app

### "I want to build a Pexip video calling app from scratch."

**Should trigger:** `signals-pattern`, `call-lifecycle`, `media-pipeline`, `preflight`

**Good output:** Claude lays out the architectural foundation — service layer wrapping `@pexip/infinity` and `@pexip/media`, signal hubs as the spine, services emit signals, components subscribe. Should mention the order: signals first, then InfinityClient setup, then media pipeline, then preflight UI.

---

### "Set up the InfinityClient and the basic call flow."

**Should trigger:** `call-lifecycle`, `signals-pattern`

**Good output:** Claude shows `createInfinityClient(infinityClientSignals, callSignals)`, the four signal handlers you must wire (`onPinRequired`, `onConnected`, `onCallConnected`, `onPeerDisconnect`), and explains why `clientMute` must run on `onConnected` even if the user hasn't touched mute yet (MCU treats it as source of truth).

---

### "What's the minimum viable media pipeline?"

**Should trigger:** `media-pipeline`

**Good output:** `createMedia({...})` with empty processor arrays, a `getDefaultConstraints()` returning audio + video shapes, the `mediaSignals.onMediaChanged` wire to `infinityClient.setStream(stream)`. Should explicitly note "you can add denoise/blur later as processors."

---

## 🎯 Specific features

### "How do I add background blur?"

**Should trigger:** `media-pipeline` (with `video-effects.md` referenced)

**Good output:** Claude shows `createSegmenter` + `createCanvasTransform` + `createVideoStreamProcess`, explains that the segmenter needs MediaPipe Tasks Vision WASM + a `.tflite` model file, mentions `videoSegmentation: 'blur'` constraint and the `backgroundBlurAmount` config key. Should mention GPU vs CPU delegate trade-off.

---

### "How do I add screen sharing?"

**Should trigger:** `presentation`, `media-pipeline` (audio-processing for the audio mix)

**Good output:** Claude shows `usePresentation` from `@pexip/media-components`, wraps `getDisplayMedia` with `createGetDisplayMedia`, shows the error mapping for `NotAllowedError` / `NotFoundError` / `MonitorSharingNotAllowed`, and explains the audio content-hint switch when presentation has audio.

---

### "Add chat to the meeting with optimistic UI."

**Should trigger:** `chat`

**Good output:** Claude shows `sendMessage` adding a `pending: true` message, the `await infinity.sendMessage` call, the success path that replaces the pending entry, and the **retry queue path** using `infinityClientSignals.onRetryQueueFlushed.addOnce(...)`. Should mention the `CHARACTER_LIMIT` filter on incoming.

---

### "How do direct messages work in Pexip?"

**Should trigger:** `chat` → `direct-messages.md`

**Good output:** Claude explains the three Map structures (`directChatMessages`, `unreadDirectChatMessages`, `unseenUnreadDirectChatMessages`), the Map reordering pattern (`delete` then `set` to move thread to most-recent), and the difference between unread and unseen.

---

### "How do I render a participant list with hosts on top?"

**Should trigger:** `participants`

**Good output:** Claude shows `meeting.getParticipants({filterBy: GroupKey.InMeeting})` and explains the sort is **automatic** (hosts first alphabetically, then guests alphabetically). Should note this is the only filter that does that custom sort — `RaisedHand` sorts by `handRaisedTime`, others alphabetically.

---

### "Open breakout rooms when a host clicks a button."

**Should trigger:** `breakouts`

**Good output:** Claude shows `meeting.openRooms([...])` with the `BreakoutRoomDetail` shape, mentions the `MainBreakoutRoomId` reserved name, the `end_action: 'transfer'` field, and `guests_allowed_to_leave`. Should mention the assignment options (auto vs manual).

---

### "How do I let users change the layout?"

**Should trigger:** `layouts`

**Good output:** Claude shows `meeting.changeLayout(layoutName)`, the `MeetingLayout` component from `@pexip/media-components`, the `availableLayouts` + `layoutSvgs` server fetch, and the SVG color-replacement hack. Should mention `lecture` service type needing `guest_layout`.

---

### "Add live captions with an overlay."

**Should trigger:** `live-captions`

**Good output:** Claude shows the `useLiveCaptions` hook with the auto-clear timer (5000ms), the interim-vs-final discrimination with the length check (avoids flicker), and `useLiveCaptionsAvailable` for the toggle gate.

---

### "Add far-end camera control."

**Should trigger:** `fecc`

**Good output:** Claude explains the three gates (conference allowed, remote user opted in, browser PTZ supported), shows `browserSupportsPtzConstraints()`, the `pan/tilt/zoom` constraints in `getDefaultConstraints`, and `meeting.fecc({participantUuid, action, direction})`. Should mention this is rare and PTZ requires real hardware.

---

## 🔧 Resilience & monitoring

### "Why is the user getting spammed with 'failed to send' toasts during reconnect?"

**Should trigger:** `reconnect`

**Good output:** Claude diagnoses: every `infinityClientSignals.onFailedRequest` is firing a toast independently. The fix is `useOnFailedInfinityRequest(networkState)` which only subscribes when *not* `Reconnecting`. Should show the hook's exact 20-line implementation.

---

### "How do I show a 'reconnecting' banner?"

**Should trigger:** `reconnect`

**Good output:** Claude shows `useNetworkState(callSignals.onReconnecting, callSignals.onReconnected)` and `<NetworkAlert networkState={networkState} />`. Should mention the network state must be passed down to media components too so they can dim the local video tile.

---

### "Recover the call when the peer connection dies."

**Should trigger:** `call-lifecycle`

**Good output:** Claude shows the `onPeerDisconnect` handler calling `infinity.restartCall(callArgs)`, with `callStage = Restarting`, and mentions the `onCallConnected` recovery branch that resumes presentation if it was active. Should explicitly say "don't tear down and rejoin — use restartCall."

---

### "Surface call-quality info to the user."

**Should trigger:** `stats-monitoring`

**Good output:** Claude shows `callSignals.onCallQuality` (the 0–3 `Quality` enum) for a banner, OR `callSignals.onRtcStats` for granular detail (resolution, FPS, `qualityLimitationReason`). Should note the **log-on-change pattern** webapp3 uses to avoid noise.

---

### "What's `qualityLimitationReason` and why does it matter?"

**Should trigger:** `stats-monitoring`

**Good output:** Claude explains the four values (`'cpu' | 'bandwidth' | 'other' | 'none'`), notes that `'cpu'` is the most actionable (close other apps), `'bandwidth'` is the user's network, and `'other'` is rare. Should mention `fpsVolatility` as a related signal.

---

## 🐛 Debugging specific bugs

### "My video tile shows black after toggling blur on/off."

**Should trigger:** `media-pipeline` → `self-healing.md`

**Good output:** Claude diagnoses: the segmenter restarted but the track is stuck muted. The fix is the `ProcessorRestarted` listener with a 1000ms watchdog — if `track.muted` after the timeout, re-request `getUserMedia`. Should reference `TIME_WAIT_FOR_MUTED_TRACK_RECOVERY_MS`.

---

### "When I unmute mid-call, sometimes the server still thinks I'm muted."

**Should trigger:** `call-lifecycle` (reference.md), possibly `participants`

**Good output:** Claude explains the dual mute model: `clientMute` is local-state sync, `mute({mute: false})` is the server-side action. The full `handleAudioMute` debounce pattern (800ms) shows when both are needed (host muted you, you must request unmute via `mute` after `guestsCanUnmute` check).

---

### "Chat messages disappear when the user gets transferred to a breakout."

**Should trigger:** `chat`, `breakouts`, `call-lifecycle/transfer-flow.md`

**Good output:** Claude explains: breakout transfers use `target: 'conference'`, which clears chat. If you want chat preserved across direct-media transfers (`target: 'direct'` or `'transcoded'`), the `prevMeetingAttrs` snapshot pattern carries it. For breakout chat, that's by design — each room has its own chat scope.

---

### "Effects modal works in preflight but not after joining the call."

**Should trigger:** `preflight`, `media-pipeline`

**Good output:** Claude diagnoses: the preview pipeline (smaller dims, separate segmenter) and the main pipeline (full res) are different `MediaService` instances. Effects config writes through to a shared `config` object, so the value sticks — but the *processor* must be active in the main pipeline. Check `videoProcessor` in `Media.service.ts`.

---

### "Why does the participant list re-render every time someone toggles their mic?"

**Should trigger:** `participants`, `signals-pattern`

**Good output:** Claude explains: `infinityClientSignals.onParticipantUpdated` is a **batched** signal, so `participants.get(...)` results stay stable — but if you're calling `getCurrent(pid)` in a render loop, every mic toggle fires a re-render. Solution: subscribe via `useSyncExternalStore` to only the field you care about, or use the cache via `participants.get`.

---

## 🎨 Branding & customization

### "Brand the app for a customer with their colors and logo."

**Should trigger:** `branding-manifest`

**Good output:** Claude walks through `manifest.json` setup: `colorPalette` (11 hex colors), `images.logo`, `images.background`, `brandName`, `appTitle`. Mentions the apply order in `useBrandingLoader` and `getBrandingPath` for relative paths. Should note the `colorPalette` length validation.

---

### "Hide the chat button via branding."

**Should trigger:** `branding-manifest`

**Good output:** Claude shows `applicationConfig.hiddenFunctionality: ['button-chat']` in manifest.json, the `transformHiddenFunctionalityArrayToObject` for O(1) lookup, and `isFunctionalityHiddenByBranding('button-chat')` at the render site.

---

### "Add a terms-of-service step before users join."

**Should trigger:** `branding-manifest`

**Good output:** Claude shows `customStepConfig` in manifest.json (`active`, `source.default`, `confirmation: 'checkbox'`, `mandatory: true`), the iframe rendering, and the `custom-step` translation block for the title/button text.

---

### "Prevent users from sharing their entire screen."

**Should trigger:** `presentation`, `branding-manifest`

**Good output:** Claude shows `applicationConfig.monitorTypeSurfaces: 'exclude'` in manifest.json. Should mention this triggers the `MonitorSharingNotAllowed` error if the user picks a monitor anyway, and webapp3's error mapping shows a localized "Sharing the entire screen is not allowed" toast.

---

## 🔌 Plugins

### "Build a plugin that adds a 'Save transcript' button to the toolbar."

**Should trigger:** `plugin-host` (host side), but Claude should also note the *plugin author* side is documented in Pexip's separate plugin docs.

**Good output:** Claude shows the host-side `manifest.json` plugin entry, the iframe sandboxing, the `ui:button:add` RPC payload shape that the plugin sends, and how the host's `handleAddButton` updates `pluginsElements` state. Should warn about the plugin/widget split.

---

### "Subscribe my plugin to participant join events."

**Should trigger:** `plugin-host`, `participants`

**Good output:** Claude explains: the plugin host forwards `infinityClientSignals.onParticipantJoined` to all registered channels via `event:participants`. Plugin code subscribes via `Channel.addEventListener('event:participants', handler)`. Should mention initial-sync replays past state.

---

## 🛡️ Edge cases & resilience

### "What happens if the user closes the tab mid-call?"

**Should trigger:** `call-lifecycle`, `browser-close-confirmation`

**Good output:** Claude explains the **two layers**: `pagehide` event triggers `disconnect({reason: 'Browser closed'})` at the SDK level (frees the slot), and `beforeunload` shows the "Are you sure?" prompt. Two separate browser events, two handlers.

---

### "Why does the 'Are you sure you want to leave?' prompt sometimes not show?"

**Should trigger:** `browser-close-confirmation`

**Good output:** Claude lists the cases: mobile Safari ignores `beforeunload` entirely; tabs that haven't received user interaction don't prompt; the `enableBrowserCloseConfirmationByDefault` brand setting and user override interact in a 3-state way. Should reference the `BrowserCloseConfirmation` enum.

---

### "Network drops for 30 seconds — what should happen?"

**Should trigger:** `reconnect`, `call-lifecycle`

**Good output:** Claude walks through the timeline: `onPeerDisconnect` fires → `restartCall` runs → `callSignals.onReconnecting` → UI shows banner via `<NetworkAlert>` → `useOnFailedInfinityRequest` detaches its toast subscriber → eventually `onCallConnected` fires with `callStage === Restarting` → presentation resumes if active → `onReconnected` clears the banner.

---

### "Direct-media transfer happens — what state should I preserve?"

**Should trigger:** `call-lifecycle/transfer-flow.md`

**Good output:** Claude shows the `prevMeetingAttrs` snapshot in the outer `handleTransfer` handler: chat messages, direct chat messages, unread/unseen, participants, activities, captions enabled. The new `Meeting` instance accepts these via `meetingAttrs` constructor param. Resets to `{}` after consumption.

---

## 🤔 Conceptual / architectural

### "Why does webapp3 use signals everywhere instead of React state?"

**Should trigger:** `signals-pattern`

**Good output:** Claude explains: SDK events fire faster than React renders; many components need the same data; render-thrashing during transfer/reconnect is real. Signals decouple the SDK firehose from React's render cycle. Should mention the four variants (generic / behavior / replay / batched) and when to use each.

---

### "Should I use `useState` or a signal for X?"

**Should trigger:** `signals-pattern`

**Good output:** Claude offers the heuristic: ephemeral UI state (modal open, hover, drag position) → `useState`. SDK-derived state, multi-component state, or anything that can update from outside React → signal. The "current value" case → behavior signal so new subscribers don't miss it.

---

### "How are skills in this bundle organized?"

**Should trigger:** Claude reads `ARCHITECTURE.md` directly

**Good output:** Claude shows the dependency graph (signals-pattern at the root), the three tiers (Foundation / Features / Integration), and offers a reading order based on what the user is building.

---

## 🔀 Cross-skill / multi-step

### "I'm starting a new Pexip-based meeting app. Walk me through end-to-end."

**Should trigger:** `signals-pattern`, `call-lifecycle`, `media-pipeline`, `preflight`, `reconnect` (and probably surface `chat`, `participants`)

**Good output:** Claude orchestrates: (1) set up signal hubs, (2) wrap `@pexip/infinity` in a service, (3) wrap `@pexip/media` in a service, (4) wire `mediaSignals.onMediaChanged → infinityClient.setStream`, (5) build preflight UI with `@pexip/media-components` hooks, (6) wire `useNetworkState` + `useOnFailedInfinityRequest` for resilience, (7) join with `infinityClient.call({mediaStream, ...})`. Then offer to add features.

---

### "I have an existing Pexip app on an old SDK version. What do I need to update?"

**Should trigger:** Claude reads `ARCHITECTURE.md` (versioning policy section) and surfaces multiple skills

**Good output:** Claude lists the version-sensitive things: `callType` string format, manifest schema version, new signals on `infinityClientSignals`. Recommends running `tsc` first to surface breaking changes, then diffing your version's webapp3 source against the skill's reference paths.

---

### "I want to ship branding presets so customers can pick from 5 themes."

**Should trigger:** `branding-manifest` (and possibly `plugin-host` if themes include plugins)

**Good output:** Claude explains: each preset is a separate branding folder served from a different web app path. The `applicationConfig.bgImageAssets` lets each preset ship multiple background options. The `colorPalette` is the primary theming hook; everything else (logo, jumbotron, custom step) layers on top.

---

## 🧪 If a prompt doesn't fire the expected skill

The skill's `description` frontmatter needs more specific keywords. To diagnose:

1. Open the failing prompt in a fresh Claude Code session in this repo
2. Note which skill (if any) Claude invoked
3. Compare the prompt's actual phrasing against the skill's `description` field
4. Add the missing trigger phrases to the description (e.g. error message verbatim, function name, symptom keywords)
5. Reload the session and retest

The descriptions follow CSO ("SEO for LLMs") principles — they should list specific symptoms, error messages, function names, and trigger phrases. Avoid generic words like "Pexip" alone since that's in every skill.

---

## 🎓 For developers learning Pexip

If you're using these skills as a learning resource (not just reference), good prompts:

- **"Explain how webapp3 handles peer disconnect."** — gets the full ICE-restart flow with state machine
- **"Walk me through what happens between 'click join' and 'video appears'."** — gets the full lifecycle
- **"Why does webapp3 have a separate preview pipeline?"** — gets the architectural reasoning
- **"What's the most common bug Pexip teams hit when adding chat?"** — gets the optimistic UI / retry queue gotcha
- **"Compare how webapp3 handles transfer vs reconnect."** — gets a comparative explanation of two related but distinct flows

These work well because they're *educational* prompts that ask Claude to synthesize across multiple skills. Each skill alone is reference material; the synthesis comes from asking the right questions.
