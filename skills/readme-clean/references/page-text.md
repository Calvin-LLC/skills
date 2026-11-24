# Page and site text

For text that is read at a glance, not read through: an HTML caption page, a demo walkthrough, a standup page, a status dashboard, a run log digest. The Workflow in `SKILL.md` still applies. These rules set the register.

## One line of action, one line of state

Each step gets one line of what is happening plus one line of the state it is in. Cut anything the heading already carries (the order number, the timestamp, the step name) and anything the reader cannot act on (raw API response bodies, JSON blobs). Keep every number, identifier, and code reference, phrased plainly. The target line reads like "Cookies cleared. The account is logged out. DB now: no session. Profile blob 0 bytes."

## Step titles use the everyday word

Never the internal or technical term. A reader scanning the page should recognise the step without knowing the domain. "Interstitial" becomes "Loading", "Device-approval wall" becomes "Approval asked", "Two-factor method" becomes "Where to send the code", "Captcha wall: where the re-run stopped" becomes "Waiting for a person". If a title names a state machine value or a field name, rewrite it as what a person sees.

## Strip provenance

Run ids, capture timestamps, frame numbers, script filenames, and phrases like "captured at" belong in the evidence manifest, not in the words a reader scans. Keep the number when it is the fact (a byte count, a duration, a state name). Drop the machinery that produced it.

## Captions must match the artifact

A caption that describes a state the artifact does not show is worse than no caption: the reader trusts the page and is wrong. Cut the sentence or the whole step.
