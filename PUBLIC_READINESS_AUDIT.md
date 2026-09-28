# Public readiness

This repository is a fresh portfolio project with independently initialized Git history. It contains only reviewed workflow code, documentation and synthetic examples. No production history was imported.

## Scope

- Market events, prices, sectors, sentiment and the fictional watchlist in `examples/` are synthetic.
- Production publishing configuration, credentials and analytics identifiers are excluded.
- The optional watchlist in configuration uses generic, widely followed market ETFs for workflow illustration; it is not a recommendation list.
- No employer or customer records, internal research, or investment performance claims are included in the intended content.
- No software license is included; the repository owner should select one deliberately.

## Validation

The CI workflow regenerates the HTML example, verifies that expected placeholders have been replaced, and runs the public-content scanner on Python 3.11, 3.12 and 3.13. Before the first push, local validation on Python 3.13.2 passed: deterministic offline regeneration, placeholder/script/external-URL checks, privacy scanning, and a synthetic secret-detection probe whose value was redacted. The GitHub Actions matrix is pending its first remote run.

The privacy scanner reports file paths and categories without printing matched values. It detects common credential formats, private-key blocks, personal filesystem paths, email addresses, and selected production identifiers. It is a heuristic check, not a security certification.

## Human review boundary

AI assists research and drafting. Humans remain responsible for checking primary sources, selecting news, interpreting relevance, reviewing the rendered report and approving publication. The offline sample makes no claims about actual market events.

## Disclaimer

This repository is a personal research and engineering project for informational and educational purposes only. It is not investment advice and is not affiliated with, sponsored by, or endorsed by my employer.
