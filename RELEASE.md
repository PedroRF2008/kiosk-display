# Release Process

1. Update version numbers:
   - Update VERSION and VERSION_CODE in `display/version.py`
   - Commit changes: `git commit -am "Bump version to x.x.x"`

2. Create and push tag:
   ```bash
   git tag -a vX.X.X -m "Version X.X.X"
   git push origin vX.X.X
   ```

3. The GitHub Action will automatically:
   - Create a ZIP file of the display directory
   - Generate SHA256 checksum
   - Create a GitHub release
   - Upload the ZIP and checksum files

4. Update Firestore:
   ```javascript
   {
     "config/versions": {
       "latestVersion": "X.X.X",
       "latestVersionCode": XX,
       "versions": {
         "X.X.X": {
           "downloadUrl": "https://github.com/USER/REPO/releases/download/vX.X.X/kiosk-vX.X.X.zip",
           "sha256": "checksum-from-release",
           "releaseDate": "2024-XX-XX",
           "changelog": "Description of changes"
         }
       }
     }
   }
   ```