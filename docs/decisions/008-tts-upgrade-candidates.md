# ADR 008: TTS Upgrade Candidates

**Status**: 🕵️ Investigation
**Date**: 2026-04-17
**Deciders**: Team
**Tags**: tts, audio, models, research

## Context

The main branch defaults to ElevenLabs for text-to-speech. The first local
alternative (Microsoft **VibeVoice**) is still an unmerged feature branch
(PR #94). Two high-profile open-weight TTS models landed in Q1 2026 that
warrant evaluation before we commit to a single primary TTS stack:

- **VoxCPM2** (OpenBMB, April 2026) — 2B params, 30 languages, 48 kHz
  studio-quality output, includes a "Voice Design" feature that creates
  a brand-new voice from a natural-language description.
- **Mistral Voxtral TTS** (March 2026) — 9 languages, ~70 ms latency,
  3-second voice cloning, open-weight.

Hardware in play: a remote machine with an NVIDIA A5000 (24 GB VRAM) is
available over SSH, plus a MacBook Air for local dev. Any of the
candidates below run on the A5000; **NeuTTS Air** is the only one that
plausibly runs on the MacBook directly.

## Candidates

| Model | Released | Params | Latency | Max Quality | Multi-speaker | License | Notes |
|---|---|---|---|---|---|---|---|
| **VibeVoice** (Microsoft) | 2025 | 1.5B | moderate | 24 kHz | ✅ up to 4 speakers, 90 min | MIT | Best long-form multi-speaker dialogue, already integrated on PR #94 |
| **VoxCPM2** (OpenBMB) | Apr 2026 | 2B | moderate | 48 kHz | ⚠️ via multiple calls | Apache-2.0 | Highest audio quality, 30-lang, Voice Design from prompts |
| **Voxtral TTS** (Mistral) | Mar 2026 | unspecified | 70 ms | 24 kHz | ⚠️ via multiple calls | Apache-2.0 | Lowest latency, 3-second cloning, 9-lang |
| **NeuTTS Air** (Neuphonic) | 2025 | 0.5B | fast | 24 kHz | ❌ single-voice | Apache-2.0 | Runs on-device; laptop-only fallback |

## Recommendation

**Keep VibeVoice as the primary target** — long-form, multi-speaker
dialogue is the podcast's core workload, and no other open-weight entry
currently beats VibeVoice on that axis. Merge PR #94 as the baseline.

**Run a side-by-side listening test vs. VoxCPM2** before switching. The
48 kHz studio-quality ceiling and Voice Design feature are genuinely
compelling, but the format (single-speaker-per-call) is a worse fit for
the project's script block structure (`speaker` + `text`) and would
require stitching per-speaker audio after the fact.

**Voxtral is a strong secondary for latency-sensitive modes** (e.g. a
future "live preview" on the admin page) but is not a replacement for
the main generation pipeline.

**NeuTTS Air** is the right fallback for laptop-only local dev if we
want TTS without SSHing into the remote box.

## Next steps

1. Merge PR #94 to land VibeVoice as the reference local TTS.
2. Stand up a small comparison harness that renders the same script
   block through VibeVoice and VoxCPM2 on the A5000, then collect
   human rating on naturalness, pacing, and speaker consistency.
3. Open a follow-up code issue to add a `VoxCPM2Provider` under
   `src/services/tts/` if/when VoxCPM2 wins the bake-off — reuse the
   existing `BaseTTSProvider` + `TTSProviderFactory` pattern.

## References

- VibeVoice: https://microsoft.github.io/VibeVoice/
- VoxCPM2: https://github.com/OpenBMB/VoxCPM
- Voxtral TTS: https://mistral.ai (announced 2026-03-23)
- NeuTTS Air: https://neuphonic.com
