name: Update Wave Forecast Card

on:
  schedule:
    - cron: '0 */4 * * *'
  workflow_dispatch:

jobs:
  generate-and-update:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests beautifulsoup4 pillow

      - name: Remove old card
        run: rm -f wave_card.png || true

      - name: Generate card
        run: python generate_wave_card.py

      - name: Verify file
        run: |
          if [ -f wave_card.png ]; then
            echo "Card generated!"
            ls -la wave_card.png
            du -h wave_card.png
          else
            echo "ERROR: Card NOT generated"
            exit 1
          fi

      - name: Commit and push changes
        run: |
          git config user.name "GitHub Actions Bot"
          git config user.email "actions@github.com"

          git add wave_card.png

          if git diff --cached --quiet; then
            echo "No changes to commit"
            exit 0
          fi

          git commit -m "Update wave forecast card [auto]"
          git push origin main
