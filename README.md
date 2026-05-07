<p align="center">
  <img src="./pexip.svg" width="120" alt="Pexip">
</p>

# awesome-pexip-skills

[![lint](https://github.com/Josh-E-S/awesome-pexip-skills/actions/workflows/lint.yml/badge.svg)](https://github.com/Josh-E-S/awesome-pexip-skills/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

A Claude Code skill bundle for building [Pexip Infinity](https://www.pexip.com/) video calling apps.

These skills distill patterns from Pexip's official **webapp3 v40-12.0** reference implementation: the production webapp Pexip ships with Pexip Infinity. The patterns are battle-tested in production.

**17 skills, ~6,000 lines of distilled patterns.** New to webapp3? Read [`ARCHITECTURE.md`](./ARCHITECTURE.md) first.

## What's inside

### Intake (fires on open-ended project requests)

| Skill | When it triggers |
|---|---|
| [`project-intake`](./skills/project-intake/SKILL.md) | "I want to build a Pexip app" / "add Pexip to my app" / open-ended new-project requests. Asks 3–4 scoping questions, then routes to the right skills. Won't fabricate test endpoints. |

### Foundation (read first)

| Skill | When it triggers |
|---|---|
| [`signals-pattern`](./skills/signals-pattern/SKILL.md) | Designing the `@pexip/signal` pub/sub architecture; when to add a signal hub vs use React state |
| [`call-lifecycle`](./skills/call-lifecycle/SKILL.md) | `createInfinityClient`, joining/leaving, pin/IDP/extension flows, ICE restart, transfers between conferences |
| [`media-pipeline`](./skills/media-pipeline/SKILL.md) | `createMedia` + audio/video processors, denoise, MediaPipe blur/replace, audio mixing, self-healing tracks |
| [`preflight`](./skills/preflight/SKILL.md) | Device enumeration, permission UX, mic/camera test, blocked-permission help screens |
| [`reconnect`](./skills/reconnect/SKILL.md) | `NetworkState` coordination, suppressing toast spam during reconnect, `onFailedRequest` |

### Meeting features

| Skill | When it triggers |
|---|---|
| [`chat`](./skills/chat/SKILL.md) | Group + direct messages, optimistic UI, retry-queue reconciliation, character limit, unread vs unseen |
| [`participants`](./skills/participants/SKILL.md) | `GroupKey` filters, mute/kick/admit, host/guest sorting, fuzzy search, batched activity, cache invalidation graph |
| [`presentation`](./skills/presentation/SKILL.md) | Screen sharing — `getDisplayMedia`, content hints, audio mixing, ICE-restart preservation |
| [`breakouts`](./skills/breakouts/SKILL.md) | Open/edit/close rooms, auto vs manual assignment, ask-for-help, guest tokens |
| [`layouts`](./skills/layouts/SKILL.md) | Host vs personal layouts, lecture-mode guest layout, presentation-in-mix detection, SVG previews |

### Integration & polish

| Skill | When it triggers |
|---|---|
| [`branding-manifest`](./skills/branding-manifest/SKILL.md) | `manifest.json` loading, color palette, hidden functionality, custom step iframe, defaults |
| [`plugin-host`](./skills/plugin-host/SKILL.md) | `@pexip/plugin-api` integration, sandboxed iframes, panel widgets, toolbar buttons, conference RPC routing |
| [`stats-monitoring`](./skills/stats-monitoring/SKILL.md) | `onRtcStats`, `qualityLimitationReason`, `fpsVolatility`, log-on-change pattern, call quality UI |
| [`browser-close-confirmation`](./skills/browser-close-confirmation/SKILL.md) | `beforeunload` wiring, "Are you sure you want to leave?" prompt, config-driven toggle |
| [`live-captions`](./skills/live-captions/SKILL.md) | Real-time transcription overlay, interim vs final, auto-clear timer, breakout reset |
| [`fecc`](./skills/fecc/SKILL.md) | Far-end camera control (PTZ), capability detection, currently-controlling tracking |

Each skill includes a quick-start `SKILL.md`. Larger skills (`call-lifecycle`, `media-pipeline`, `chat`) have sibling `*.md` files for the deep details.

## Install

Clone the repo first:

```bash
git clone https://github.com/Josh-E-S/awesome-pexip-skills.git
```

### As a Claude Code plugin

```bash
/plugin install pexip --from-marketplace ./awesome-pexip-skills
```

### Manually in a project

```bash
cp -r awesome-pexip-skills/skills/* /path/to/your-project/.claude/skills/
```

### As a global skill set

```bash
cp -r awesome-pexip-skills/skills/* ~/.claude/skills/
```

## How to use

Open Claude Code in a Pexip project and ask natural questions. See [`PROMPTS.md`](./PROMPTS.md) for ~50 example prompts organized by goal — useful for both learning and verifying that skill triggers fire correctly.

Quick samples:

- *"How do I set up the InfinityClient?"* → `call-lifecycle`
- *"Why is my video track stuck after toggling blur?"* → `media-pipeline` (`self-healing.md`)
- *"How do direct messages work?"* → `chat` → `direct-messages.md`
- *"How do I open breakout rooms?"* → `breakouts`
- *"Why are toasts spamming during reconnect?"* → `reconnect`
- *"How do I add a custom plugin?"* → `plugin-host`
- *"Why does the manifest.json `colorPalette` need exactly 11 colors?"* → `branding-manifest`

If a skill *doesn't* fire when it should, the trigger description needs more specific keywords. Edit `SKILL.md`'s frontmatter and reload. (`PROMPTS.md` doubles as a regression-test suite for this.)

## SDKs referenced

| Package | Role | Used in skill(s) |
|---|---|---|
| `@pexip/infinity` | Signaling, call control, event source | call-lifecycle |
| `@pexip/media` | `getUserMedia`, processors | media-pipeline |
| `@pexip/media-control` | Device info, constraints | media-pipeline, presentation |
| `@pexip/media-processor` | MediaPipe segmenter, denoise | media-pipeline |
| `@pexip/media-components` | Call-aware UI hooks (preview, network state) | preflight, reconnect, presentation, layouts |
| `@pexip/signal` | Pub/sub primitive | signals-pattern (foundation) |
| `@pexip/peer-connection-stats` | RTC stats normalization | stats-monitoring |
| `@pexip/plugin-api` | Iframe RPC | plugin-host |
| `@pexip/config-manager` | Reactive config store | branding-manifest |

## Source extraction

These patterns came from reverse-engineering webapp3 v40-12.0 via source maps. The original TypeScript source for **377 application files** + **540 SDK files** (17 internal `@pexip/*` packages) was reconstructable from the `.js.map` files included in the public webapp3 download.

Each skill ends with a "Reference source" section listing the exact files the patterns came from, so you can verify against your own webapp3 version.

## Versioning policy

These skills target Pexip Infinity webapp3 v40-12.0 specifically. The SDKs evolve.

When you upgrade `@pexip/*` packages:
1. Run TypeScript compilation — most breaking changes surface as type errors
2. Watch for new signals on `infinityClientSignals` — your handlers won't break but you may miss new events
3. Diff against the skill's "Reference source" files in your new webapp3 version

The architectural patterns (signal pub/sub, optimistic-then-reconcile, state-preservation-via-snapshot) are stable. SDK function signatures change more often.

## License

MIT. See [`LICENSE`](./LICENSE).

## Contributing

This is currently an opinionated personal/team library. PRs welcome if you find a pattern that's wrong or missing — please cite the webapp3 source line for the correction.
