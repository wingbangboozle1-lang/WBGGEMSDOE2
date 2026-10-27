#!/usr/bin/env python3
"""Legacy DZ-16 renderer; its calibrated approval is revoked.

The historical page source is preserved in Git history. Rebuilding this entry
point installs fail-closed redirects rather than reinstating the old approval.
"""
from build_legacy_routes import main

if __name__ == '__main__':
    raise SystemExit(main())
