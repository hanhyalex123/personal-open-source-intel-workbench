# Release Polish Design

## Goal
Prepare the project for public sharing by making the homepage feel like an intentional Chinese intelligence station, improving the sync monitor's visual language, and rewriting the README around the product's current state instead of its original concept pitch.

## Scope
- Upgrade the homepage into a magazine-cover style landing view.
- Add a lightweight icon system without introducing a new dependency.
- Bring the sync monitor page into the same visual language.
- Rewrite the README so it matches what the product can do today.
- Prepare short Linux.do posting copy.

## Visual Direction
Use a "情报站 / 杂志封面" look rather than a generic admin dashboard:
- Stronger masthead feel on the homepage.
- Section labels that read like editorial columns.
- Simple inline icons and signal chips for quick scanning.
- Better contrast and grouping for key status surfaces.

The design should stay inside the existing layout system and keep desktop/mobile behavior intact.

## Approach
Keep the data model and routing unchanged. The work is presentation-first:
- Extend homepage components with icon-friendly wrappers and stronger hierarchy.
- Add shared CSS primitives for icons, signal badges, and cover panels.
- Update the sync monitor intro so it looks like part of the same publication.
- Rewrite README sections to reflect current architecture, current screens, startup flow, and current limits.

## Risks
- Over-styling can hurt readability. The visual upgrade should remain restrained and data-first.
- Introducing a third-party icon package is unnecessary churn. Inline SVG or Unicode-safe symbols are enough.
- README should not promise unpublished roadmap items.

## Validation
- Frontend tests must keep passing.
- Backend tests must keep passing.
- Local startup script should still serve the app on `127.0.0.1`.
