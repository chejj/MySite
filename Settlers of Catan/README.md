# Settlers of Catan

The editable Shiny application lives in `app/`. The static Shinylive export
used by GitHub Pages lives in `dashboard/`.

After changing the app, rebuild the browser bundle from the portfolio root:

```bash
python -m shinylive export "Settlers of Catan/app" "Settlers of Catan/dashboard"
```

Then render the portfolio page:

```bash
quarto render "Settlers of Catan/index.qmd" fun/index.qmd --no-clean
```
