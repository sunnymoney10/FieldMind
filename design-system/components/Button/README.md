# Button

The footer and form button; exactly one per screen is primary (`fm-btn--primary`, signal-pink with carbon text).

- Height `button-height` (48px), radius `radius-md`, label in sentence case, one or two words: "Log visit", "Save visit", "Research".
- Secondary buttons are `surface` with a 1.5px `ink` border. Never a second pink button on the same screen.
- Primary actions live at the bottom of the screen, in thumb reach.
- The consumer provides the label and the click handler; use a real `<button>`.
