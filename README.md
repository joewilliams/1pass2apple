# 1Password to Apple Password Converter

This script attempts to mangle 1password .1pif file formated exports into an Apple Password CSV import file.

If you have exported the 1password vault as 1pif file you should be able to do something like this:
```
python3 mangle.py ./data.1pif output
```

The resulting CSV should import correctly in Apple Passwords. Including secure notes and OTP URIs.

## Caveats

The 1pif format includes a few different possible fields for the same value (i.e. multiple locations where you might find the password). This script attempts to find the right one and fall back to other possible locations in the json format.

This whole thing might be easier by enumerating the various `typeName` (i.e. `wallet.financial.CreditCard`, `webforms.WebForm`, etc) and creating a parser for each one. Credit cards seem like a pain for instance. Regardless, this script seems to work for 99% of the cases I have.

## Bugs

If you run into bugs please create a PR with a fix.
