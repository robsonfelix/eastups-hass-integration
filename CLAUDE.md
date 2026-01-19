# EAST UPS Integration - Development Notes

## Deployment

```bash
cd /homeassistant/src/eastups-hass-integration

# Commit changes
git add -A && git commit -m "Description"

# Push
git push origin main

# Create release (HACS requires releases, not just tags)
gh release create v1.x.x --title "v1.x.x - Title" --notes "Release notes"
```

## Local Testing

```bash
# Symlink to HA custom_components
ln -sf /homeassistant/src/eastups-hass-integration/custom_components/east_ups /homeassistant/custom_components/east_ups

# Restart HA
ha core restart
```

## Register Map

Based on reverse engineering EA900 G4 (Intelbras DNB 6kVA). Register definitions in `const.py`.

Key differences from EA660 G4 documentation:
- Input Voltage @ reg 0 (not 12)
- Output Voltage @ reg 24 (not 12)
- Battery Status @ reg 71 (not 48)
- Running Time @ reg 27 in weeks (not 32-bit seconds)
