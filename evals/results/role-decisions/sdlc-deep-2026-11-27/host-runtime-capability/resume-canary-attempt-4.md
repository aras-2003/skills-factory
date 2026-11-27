# Runtime resume canary — attempt 4

Candidate `f51c4fad6aceeab545943812794f6f44132239fc`. The same-marker A→interrupt→B scenario completed in two distinct App Server threads. A thread `01a21e6a-9406-7ab1-ac82-645b7f1f6ecb`, turn `01a21e6a-9666-7ee2-93cb-c3fc4025f308`, used host-reported `workspaceWrite`; it created the exact marker (SHA-256 `51fcc3c5aa356824b871e6d6bc5f22c9b342298c40c9b282a614e05f78fd89be`), entered the bounded wait, accepted `turn/interrupt`, and produced correlated terminal status `interrupted`.

The coordinator removed the verified marker and confirmed it absent. The serialized handoff passed `delegation_handoff.serialize_input`, length 1,902 bytes, SHA-256 `dda3b8c99378fa7c8b59649b6f3aa52871c9eaea072f0181b5dea6ce85f26dae`. B was a distinct thread `01a21e6a-ca12-77b0-b185-39c42ce32a9a`, turn `01a21e6a-cab1-7ce1-8824-72b7189c17ce`; thread/start reported `gpt-6.1-terra`, high, `readOnly`; its turn completed. Scratch candidate remained exact and Git status clean; marker remained absent.

**Disposition: PARTIAL.** The outer command output was truncated before the B command event's structured denial fields could be inspected or durably retained. Therefore this attempt does not prove an OS-level denial, even though the B session was read-only and marker absent. No MCP calls or approval request/transfer was recorded. Do not merge evidence with attempt 3.
