# Design critique

**Scope and evidence.** Reviewed only `checkout-single.png`, a supplied 1920 × 902 desktop screenshot. Task: a returning customer reviews the order summary and finds the next step. The image explicitly identifies itself as a synthetic fixture; no operational behavior is represented. Checkout rules, actual order data, and the next destination are unknown.

**Overall read.** “Checkout” → “Review order” → item/total → instruction → “Continue” provides a readable top-to-bottom structure. The first priority is making the summary and next action meaningful: both currently depend on placeholder content.

**Findings**

1. **Major · High confidence — The order cannot be meaningfully reviewed from the displayed content.**
   - **Visible evidence:** In the upper-left review card, the only item label is “Item”; its amount is “[item total]”, and the total is “[order total]”. No identifiable product or real amount is shown.
   - **Likely consequence:** The customer lacks the information needed to confirm what they are ordering and the amount they will pay. This concerns the supplied state; it does not establish that a live checkout has missing data.
   - **Specific repair:** Replace the generic row with the actual item name, quantity and amount, and display the actual order total with its currency. Give the total stronger typographic emphasis than the item row.

2. **Major · High confidence — The next step is unspecified.**
   - **Visible evidence:** The text above the button reads “[next step description]”; the button itself says only “Continue”.
   - **Likely consequence:** The customer can locate an action but cannot tell what it leads to or whether another review stage follows.
   - **Specific repair:** Replace the placeholder with a short explanation of the actual next stage, then name that stage in the button label. For example, use “Continue to payment” only if payment is truly next. If the action submits the order, its wording should explicitly communicate that commitment.

3. **Moderate · Medium confidence — The only next-action control has weak visual prominence.**
   - **Visible evidence:** “Continue” is rendered as gray text inside a thin gray outline on the white card. It has no stronger color or fill than nearby supporting elements.
   - **Likely consequence:** It may read as secondary or unavailable, making the next step less obvious. The screenshot cannot establish whether it is disabled.
   - **Specific repair:** Give the available primary action a clearly differentiated filled treatment and readable label contrast. If it is intentionally unavailable, show the prerequisite beside it and visually distinguish its disabled state from an enabled primary button.

**Needs verification.** In an interactive version, check that the action reaches the stated destination, that its enabled/disabled state matches the explanation, and that keyboard focus and screen-reader naming are clear. Measure text/control contrast; this image does not establish a numeric accessibility result. Check narrow-screen reflow separately; no mobile behavior was supplied.

**Recommended order.** Populate meaningful summary values; clarify the next stage and button wording; strengthen the action’s visual prominence. Then verify those states and behaviors in the working interface.
