# Architecture overview

This doc explains how the 16 skills in this bundle relate to each other and to the underlying Pexip SDKs. Read this before diving into individual skills if you're new to webapp3 — it's the orientation map.

## The big picture

Every Pexip web app is built around **three things talking to each other**:

```
                ┌──────────────────────────────┐
                │       React UI tree          │
                │  (pages, viewModels, views)  │
                └──────────────▲───────────────┘
                               │ subscribes to signals,
                               │ calls service methods
                               │
                ┌──────────────┴───────────────┐
                │     Service layer            │  ← Your app's logic
                │ Infinity.service             │
                │ Media.service                │
                │ Image.service                │
                │ Plugin host                  │
                └─────┬─────────────────┬──────┘
                      │ wraps          │ wraps
                      ▼                 ▼
            ┌─────────────────┬─────────────────┐
            │  @pexip/infinity│  @pexip/media   │
            │  (signaling +   │  (getUserMedia +│
            │   call control) │   processors)   │
            └─────────┬───────┴─────────┬───────┘
                      │                 │
            ┌─────────┴───────┐ ┌───────┴────────────┐
            │ @pexip/peer-    │ │ @pexip/media-      │
            │ connection      │ │ processor          │
            │ (RTCPeer wrap)  │ │ (MediaPipe, denoise)│
            └─────────────────┘ └────────────────────┘

    Cross-cutting:  @pexip/signal     @pexip/components    @pexip/media-components
                    (pub/sub)         (UI primitives)      (call-aware UI hooks)
```

The pattern that makes webapp3 work: **service modules wrap the SDK and emit signals**. Components subscribe to signals. Almost zero React state for SDK data.

If you remember nothing else, remember that. Everything below elaborates on it.

## Skill dependency graph

```dot
    project-intake  ◄─── (fires on open-ended new-project requests; routes to others)
         │
         ▼
    signals-pattern  ◄─── (read this first, everything depends on it)
         │
         ├─► call-lifecycle ◄─── (the heart of the app)
         │       │
         │       ├─► reconnect (UI for ICE restart)
         │       ├─► chat (signaling-channel messages)
         │       ├─► participants (event-driven roster)
         │       ├─► layouts (server-side composition)
         │       ├─► breakouts (sub-conferences)
         │       └─► live-captions (transcription stream)
         │
         ├─► media-pipeline ◄─── (the other heart)
         │       │
         │       ├─► preflight (UI for the pipeline before joining)
         │       ├─► presentation (screen-share track)
         │       └─► fecc (PTZ camera control)
         │
         ├─► branding-manifest (configures everything)
         │
         ├─► plugin-host (extends everything via iframes)
         │
         ├─► browser-close-confirmation (small but important)
         │
         └─► stats-monitoring (observability over the whole stack)
```

## Recommended reading order

### If you've never seen Pexip's SDKs:

1. **`signals-pattern`** — the pub/sub spine
2. **`call-lifecycle/SKILL.md`** — the state machines and event-handler shape
3. **`media-pipeline/SKILL.md`** — `createMedia` and how processors plug in
4. **`preflight/SKILL.md`** — what runs before the call

That's enough to build a basic Pexip app. The rest are features.

### If you're adding a specific feature:

| Goal | Skills to read |
|---|---|
| "Just a basic call with mute/cam toggle" | signals-pattern → call-lifecycle → media-pipeline → preflight → reconnect |
| Add chat | + chat |
| Add participant list | + participants |
| Add screen sharing | + presentation |
| Add background blur | media-pipeline/video-effects.md (already inside media-pipeline) |
| Add custom layouts UI | + layouts |
| Add breakout rooms | + breakouts (also re-read `call-lifecycle/transfer-flow.md`) |
| Add live captions | + live-captions |
| Add FECC controls | + fecc (rare; only for hardware deployments) |
| Brand the app for a customer | + branding-manifest |
| Embed a third-party iframe plugin | + plugin-host |
| Surface call-quality info | + stats-monitoring |
| Prevent accidental tab close | + browser-close-confirmation |

## Data flow: a single call's lifecycle

```
USER clicks "Join meeting.alice"
   │
   ▼
preflight runs:
   • mediaService.getUserMedia(constraints)          ← media-pipeline
   • mediaSignals.onMediaChanged emits                ← signals-pattern
   • UI renders device pickers                        ← preflight
   │
   ▼
USER clicks "Join":
   • config.set('displayName', 'Alice')               ← branding-manifest (or user-typed)
   • infinityClient.call({mediaStream, alias, ...})   ← call-lifecycle
   │
   ▼
SDK opens event stream:
   • infinityClientSignals.onConnected emits          ← signals-pattern
   • service: callStage = EventStreamConnected         ← call-lifecycle
   • service: clientMute({mute: false})               ← (mandatory initial sync)
   │
   ▼
SDK negotiates SDP:
   • callSignals.onCallConnected                       ← call-lifecycle
   • callSignals.onRemoteStream → setRemoteStream()    ← UI renders video
   • service: callStage = Connected
   │
   ▼
DURING THE CALL — events stream:
   • onMessage → chat.sendMessage / onMessage flow   ← chat
   • onParticipantJoined (batched) → groups update    ← participants
   • onLayoutOverlayTextEnabled → layout state        ← layouts
   • onLiveCaptions → caption overlay                 ← live-captions
   • onFailedRequest (if any) → toast (gated)         ← reconnect
   • onPeerDisconnect → restartCall                   ← call-lifecycle (resilience)
   • onTransfer (breakout/direct-media)               ← call-lifecycle/transfer-flow.md
   • onRtcStats (every ~1s) → log on change           ← stats-monitoring
   │
   ▼
USER clicks "End":
   • meeting.leave() → infinityClient.disconnect()    ← call-lifecycle
   • applicationConfig.disconnectDestination?         ← branding-manifest
   • mediaService cleanup, processors stopped         ← media-pipeline
   • All signal subscriptions detach                  ← signals-pattern
```

## What lives where

### App source (`src/...`)

| Concern | Files | Skill(s) |
|---|---|---|
| Service layer | `services/InfinityClient.service.ts`, `Media.service.ts`, `Image.service.ts` | call-lifecycle, media-pipeline |
| Signal hubs | `signals/*.ts` (10 files) | signals-pattern |
| React contexts | `contexts/*` | call-lifecycle, media-pipeline |
| Hooks | `hooks/*` (69 files) | every skill (each has its own hooks) |
| ViewModels | `viewModels/*` (87 files) | every skill |
| Views | `views/*` | every skill |
| Pages | `pages/*` (Home, Meeting, MeetingFlow, Preflight, etc.) | call-lifecycle, preflight |
| Plugin host | `plugins/*` (~30 files) | plugin-host |
| Branding | `branding/*` | branding-manifest |
| Config | `config.ts`, `applicationConfig.ts` | branding-manifest |
| Utils | `utils/*` | participants (createParticipants), preflight (browser detection) |

### SDK source (`pexip-sdks/...`)

| Package | Files | Skill(s) |
|---|---|---|
| `@pexip/infinity` | 11 | call-lifecycle |
| `@pexip/infinity-api` | 7 | call-lifecycle |
| `@pexip/media` | 15 | media-pipeline |
| `@pexip/media-control` | 15 | media-pipeline, presentation |
| `@pexip/media-processor` | 23 | media-pipeline (video-effects, audio-processing) |
| `@pexip/media-components` | 233 | preflight, reconnect, presentation, layouts, participants |
| `@pexip/signal` | 5 | signals-pattern |
| `@pexip/peer-connection` | 7 | (under the hood; rarely touched directly) |
| `@pexip/peer-connection-stats` | 4 | stats-monitoring |
| `@pexip/plugin-api` | 6 | plugin-host |
| `@pexip/components` | 159 | (UI library; cross-cutting) |
| `@pexip/hooks` | 14 | (utility hooks; cross-cutting) |
| `@pexip/router` | 7 | (routing; not skill-specific) |
| `@pexip/config-manager` | 8 | branding-manifest |
| `@pexip/logger` | 3 | (cross-cutting) |
| `@pexip/utils` | 20 | (cross-cutting) |

## The 10 signal hubs

| Hub | File | Purpose | Subscribed by |
|---|---|---|---|
| `infinityClientSignals` | `signals/InfinityClient.signals.ts` | Raw signaling events from SDK | call-lifecycle (heavy), reconnect, chat, participants, layouts, live-captions, plugin-host |
| `callSignals` | `signals/Call.signals.ts` | Lower-level call events (peer connection, remote stream, RTC stats) | call-lifecycle, reconnect, presentation, stats-monitoring |
| `meetingSignal*` | `signals/Meeting.signals.ts` | App-level meeting events (chat messages, splash screens, transcripts, idps) | call-lifecycle, chat, layouts, presentation |
| `MeetingFlow.signals` | `signals/MeetingFlow.signals.ts` | Join-flow step transitions | call-lifecycle, preflight |
| `InMeeting.signals` | `signals/InMeeting.signals.ts` | In-meeting UI events (search query, user-initiated disconnect) | participants, plugin-host |
| `mediaSignals` | `signals/Media.signals.ts` | Track muted/suspended/resumed/stopped, VAD, ASD | media-pipeline, preflight, call-lifecycle (debounced mute) |
| `Participant.signals` | `signals/Participant.signals.ts` | Batched participant activity (joins/leaves/changes) | participants, chat |
| `BreakoutRooms.signals` | `signals/BreakoutRooms.signals.ts` | Breakout-room lifecycle | breakouts |
| `ImageStore.signals` | `signals/ImageStore.signals.ts` | Custom background images | media-pipeline (video-effects) |
| `StepByStep.signals` | `signals/StepByStep.signals.ts` | Multi-step modals | preflight |

The first three (`infinityClientSignals`, `callSignals`, `meetingSignal*`) are the heavy ones. Most skills subscribe to one or more of these.

## Cross-skill patterns to know

### "Optimistic UI then reconcile via SDK"

Used in:
- **chat** — message added as `pending: true`, marked sent on `onRetryQueueFlushed`
- **live-captions** — UI flips immediately on toggle, rolls back on SDK failure
- **layouts** — picker updates immediately, server confirms via `onRequestedLayout`

The pattern lives in `chat/SKILL.md` first; the others reference it.

### "State preservation across recreation"

Used in:
- **call-lifecycle** (transfer-flow.md) — chat, participants, captions snapshot via `prevMeetingAttrs`
- **chat** — messages persist via the same snapshot
- **participants** — disconnected participants tracked via `oldParticipants` map

### "Behavior signal for current state, generic for events"

Used in:
- **reconnect** — `NetworkState` is behavior (replays current value to new subscribers)
- **call-lifecycle** — `MeetingFlow` step is behavior
- **media-pipeline** — `onMediaChanged` is behavior (replays current media)
- **chat** — incoming `onMessage` is generic (each event delivered once)

The choice is documented in `signals-pattern/SKILL.md`.

### "Cache invalidation via reverse-dependency graph"

Used in:
- **participants** — the most explicit example (`createReversedDependencyAdjacencyList`)

The same pattern could apply to other multi-axis state, but webapp3 only uses it once.

### "Per-browser dispatch table"

Used in:
- **preflight** — `BrowserDetection<T>` for permission help videos
- **media-pipeline** (subtly) — Safari H264 bug, mobile Safari AudioWorklet quirks

The base pattern is in `preflight/SKILL.md`.

## How webapp3 is *different* from the typical React app

If you're coming from a Redux/Zustand/Jotai background, webapp3 violates a few patterns deliberately:

1. **No central store.** State lives in service modules + signal hubs. The "store" is the network of services.
2. **Components don't dispatch actions.** They subscribe to signals and call service methods directly.
3. **Almost no `useState` for SDK data.** SDK data flows through signals. `useState` is reserved for ephemeral UI state (modal open, hover, drag position).
4. **Signal subscriptions are the dependency-array.** Effects subscribe via `signal.add(handler)` and return the detach function. No mock/stub layer.

This is closer to MobX-with-pub-sub than Redux. The advantage: the SDK's event firehose stays decoupled from React's render cycle. The disadvantage: harder to time-travel debug.

## What's NOT covered in skills

These exist in webapp3 but didn't get their own skill:

- **DTMF input** for gateway calls (small, niche)
- **AFK detection** (`useAFK.tsx` — niche; tied to AI assistant features)
- **Self-view mirroring** (one-config-flag detail; documented inline in media-pipeline)
- **Spotlight participant** (covered briefly in participants skill via `participant.spotlight()`)
- **Lock meeting** (covered briefly in call-lifecycle reference)
- **Mute all guests** (one SDK call; handled in participants)
- **Add participant** (dial-out; rare; covered briefly in plugin-host RPC list)
- **OAuth redirects** (`oauth-redirect.html` — only matters for plugins doing OAuth)
- **Theming** (`@pexip/components` ThemeProvider — handled in component library docs)
- **Routing** (`@pexip/router` — small surface; not Pexip-specific)
- **i18n** (i18next config — boilerplate; not Pexip-specific)
- **Sentry / logging** (Pino + Sentry; not Pexip-specific)

If any of these become important to your workflow, a follow-up skill is straightforward.

## Tier classification

| Tier | Skills | Why this tier |
|---|---|---|
| **Intake** | project-intake | Fires before any other skill on open-ended requests; scopes the work |
| **Foundation** | signals-pattern, call-lifecycle, media-pipeline, preflight, reconnect | Required for any working app |
| **Features** | chat, participants, presentation, breakouts, layouts | Optional but common |
| **Integration** | branding-manifest, plugin-host, browser-close-confirmation, stats-monitoring, live-captions, fecc | Used by some apps; safe to ignore until needed |

Tiers are a *reading order suggestion*, not a code-organization boundary. All 16 skills are independently invocable.

## Pexip SDK version notes

These skills target **webapp3 v40-12.0** (April 2026 build).

The SDKs evolve. Things most likely to change between versions:
- `callType` string format (changed in v39 from numeric to descriptive)
- Specific RPC method names (`breakoutRequestGuestToken` etc. — naming sometimes refactored)
- New event types added to `infinityClientSignals` (`onLiveCaptions` was newer than `onMessage`)
- Manifest schema version (currently `version: 0`)

When you upgrade `@pexip/*` packages:
1. Run TypeScript compilation — most breaking changes show up as type errors
2. Watch for new signals on `infinityClientSignals` — your existing handlers won't break, but you may miss new events
3. Re-check the `manifest.json` schema in Pexip's docs

## Where to verify if a skill goes stale

Each skill ends with a "Reference source" section listing webapp3 file paths the patterns came from. To check if a pattern still applies in a newer version:

1. Find the equivalent file in your version of webapp3
2. Diff against the file path the skill references
3. If the pattern shape is unchanged → skill is current
4. If the SDK API changed → update the skill's snippet, keep the architectural prose

The architectural patterns (signal pub/sub, optimistic-then-reconcile, state-preservation-via-snapshot) are unlikely to change. The SDK function signatures change more often.
