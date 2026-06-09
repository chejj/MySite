# Pokemon Dashboard

*This dashboard is not original as it has been edited with AI*

The editable Shiny application and its CSV files live in `app/`. The static
Shinylive export used by GitHub Pages lives in `dashboard/`.

After changing the application or its data, rebuild the browser app from the
portfolio root:

```bash
/opt/miniconda3/envs/mario/bin/shinylive export \
  "Pokemon Dashboard/app" \
  "Pokemon Dashboard/dashboard"
```

Then render the portfolio page:

```bash
/Applications/Positron.app/Contents/Resources/app/quarto/bin/quarto render \
  "Pokemon Dashboard/index.qmd" fun/index.qmd --no-clean
```
