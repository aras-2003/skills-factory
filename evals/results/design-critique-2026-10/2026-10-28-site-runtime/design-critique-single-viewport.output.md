**Design critique**

**Scope and evidence:** Reviewed `checkout-single.png`, a single 1920 × 902 desktop image showing an order-review card. Intended users and the exact checkout task are unspecified; reviewing an order and choosing “Continue” is an interpretation. Target mobile viewport is unknown.

**Overall read:** The desktop hierarchy is clear: Checkout → Review order → Total → Continue. **Mobile responsiveness cannot be confirmed from this screenshot.**

**Findings:** No mobile defect or successful mobile adaptation is established. The card’s desktop width, aligned totals, and button provide no evidence of how they reflow at narrower widths. The image also explicitly states that it represents no operational system behavior.

**Needs verification:** Please provide a screenshot of the same state at the target mobile viewport, including its width, or a runnable page to test. A mobile screenshot can establish presentation at that width; a browser test should resize through the supported mobile widths and check that the card, totals, and Continue button remain readable and reachable without clipping, overlap, or horizontal scrolling. Exercise Continue separately to verify its behavior.

**Recommended order:** Establish the target mobile width, inspect that rendered state, then test resizing and interaction. No responsive fix is justified by the desktop evidence alone.
