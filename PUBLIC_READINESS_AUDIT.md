# Public readiness

This repository is a portfolio project with independently initialized Git history. It contains reviewed workflow code, documentation, a synthetic demo and one reviewed historical HTML output. No production Git history or complete report archive was imported.

## Scope

- `examples/sample_week.json` and `examples/sample_output.html` remain a separate synthetic demonstration.
- `examples/historical/20260914.html` represents the actual September 14, 2026 report output. Its market figures, market conclusion, securities, events and calendar remain unchanged; a prominent notice identifies it as historical material, not current guidance. The owner's additional neutral wording and presentation edits are documented below.
- The historical snapshot has had its analytics scripts removed, its watchlist heading neutralized and portfolio disclaimers added. No private operational details were identified in its editorial content. See the [change record](examples/historical/README.md).
- Production publishing configuration, credentials and analytics identifiers are excluded.
- The optional watchlist in configuration uses generic, widely followed market ETFs for workflow illustration; it is not a recommendation list.
- No employer or customer records, internal research, or investment performance claims are included in the intended content.
- No software license is included; the repository owner should select one deliberately.

## Validation

The CI workflow regenerates the HTML example, verifies that expected placeholders have been replaced, and runs the public-content scanner on Python 3.11, 3.12 and 3.13. Local validation on Python 3.13.2 passed: deterministic offline regeneration, placeholder/script/external-URL checks, privacy scanning, and a synthetic credential-detection probe whose value was redacted. GitHub Actions run 36433975793 passed all three Python versions, including demo generation, placeholder/script checks and the public-content scan.

The privacy scanner reports file paths and categories without printing matched values. It detects common credential formats, private-key blocks, personal filesystem paths, email addresses, and selected production identifiers. It is a heuristic check, not a security certification.

Historical validation adds a fixed-content checksum, date/banner/disclaimer checks and detection of scripts, external resources, tracking identifiers, publishing endpoints and unresolved placeholders. The existing recursive privacy scanner includes the historical file without exemptions or weakened checks. A local comparison against the original confirmed that only documented safety edits and whitespace differ. This checks preservation of the output, not the factual accuracy of historical claims.

Local checks for this addition passed on Python 3.13.2: synthetic regeneration and HTML validation, recursive privacy scanning, and fixed historical snapshot validation. CI runs the same checks across Python 3.11–3.13.

## Final presentation edits and Pages scope

- Replaced the advisory-looking cybersecurity wording with a neutral statement identifying representative companies; the three quote links remain intact and the rest of the item is unchanged.
- Changed the historical footer to `Edited by Taylor · AI-assisted workflow`.
- Removed only two empty sentiment rows. The valid CNN Fear & Greed and VIX data remain unchanged.
- Reviewed the resulting HTML before updating its fixed checksum. The historical validator and three-version CI remain active.
- GitHub Pages assembles exactly three pages from canonical sources: the landing page, the single reviewed historical report and the synthetic demo. It does not import or publish an operational archive.
- Pages uses official GitHub actions with built-in deployment permissions and no custom secrets or production credentials. No Netlify infrastructure is included.
- Pages publication is manually triggered from `main` after approval, and the workflow requires the repository to be public. Normal CI continues independently.

## Human review boundary

AI assists research and drafting. Humans remain responsible for checking primary sources, selecting news, interpreting relevance, reviewing the rendered report and approving publication. The synthetic demo makes no claims about actual market events. The historical output did not retain news-source citations; its public quote links remain, and it is not presented as a reconstructed source-audit dataset. The historical reference to observing three cybersecurity securities is preserved as an original market observation, not rewritten as current guidance.

## Disclaimer

This repository is a personal research and engineering project for informational and educational purposes only. It is not investment advice and is not affiliated with, sponsored by, or endorsed by my employer.
