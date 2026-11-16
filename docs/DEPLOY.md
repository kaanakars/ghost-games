# Deploying the web app to Azure

One-time setup. After this, every push to `main` that passes the tests is
deployed automatically.

```
push to main ──► test (ruff + pytest, incl. every app page)
             ──► build Docker image (linux/amd64) ──► GitHub Container Registry
             ──► deploy that image to Azure App Service (Web App for Containers)
```

## 0. Tools (Mac)
```bash
brew install azure-cli
az login
```
`az login` opens the browser. Sign in with the account that has Azure for Students.

## 1. First push builds the image
Push to `main`. The `deploy` job is skipped for now (no Azure app yet), but
`test` and `build` run and the image appears under **Packages** on GitHub.

Make the package public so Azure can pull it without a password:
GitHub → your profile → **Packages** → `ghost-games` → **Package settings** →
**Change visibility** → Public.

## 2. Create the Azure resources
Pick a globally unique app name; it becomes `<name>.azurewebsites.net`.
```bash
APP=ghost-games-kaan
RG=ghost-games-rg

az group create --name $RG --location canadacentral
az appservice plan create --name ghost-games-plan --resource-group $RG --is-linux --sku B1
az webapp create --name $APP --resource-group $RG --plan ghost-games-plan \
  --container-image-name ghcr.io/akars7/ghost-games:latest
az webapp config appsettings set --name $APP --resource-group $RG --settings WEBSITES_PORT=8000
az webapp config set --name $APP --resource-group $RG --web-sockets-enabled true
```
- **Region refused?** Azure for Students only allows some regions. The error
  message lists them; use one of those instead of `canadacentral`.
- **Cost:** B1 is about US$13 a month from the student credit. To save credit,
  try `--sku F1` (free, slower to wake up), or stop the app when not needed:
  `az webapp stop --name $APP --resource-group $RG`.
- Streamlit talks to the browser over WebSockets, so they must be on (last line).

Check it: open `https://<name>.azurewebsites.net`. The first start takes a minute.

## 3. Let GitHub Actions deploy
The pipeline signs in with the app's publish profile. Newer apps have this
switched off, so allow it first:
```bash
az resource update --resource-group $RG --name scm --namespace Microsoft.Web \
  --resource-type basicPublishingCredentialsPolicies --parent sites/$APP \
  --set properties.allow=true

az webapp deployment list-publishing-profiles --name $APP --resource-group $RG --xml \
  | gh secret set AZURE_WEBAPP_PUBLISH_PROFILE
gh variable set AZURE_WEBAPP_NAME --body $APP
```
The profile goes straight from Azure into a GitHub secret, so it never shows
on screen or ends up in a file.

Re-run the workflow (Actions → CI/CD → Run workflow). All three jobs should be green.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Page loads, then "Connection error" | WebSockets off: run the last command in step 2 |
| "Application Error" | `az webapp log tail --name $APP --resource-group $RG` |
| Old version still showing | Check the deploy job used the new commit's image tag |
| Image pull failed | The GitHub package is still private (step 1) |

## Local run
```bash
pip install -r app/requirements.txt
streamlit run app/Home.py

# or the same container Azure runs:
docker buildx build --platform linux/amd64 -t ghost-games .
docker run -p 8000:8000 ghost-games      # http://localhost:8000
```
On an Apple Silicon Mac the amd64 image runs through emulation, so it's
slower locally than on Azure.

## Updating the numbers
The app reads only `app/data/`. After changing the analysis, re-export and push:
```bash
ghost-games-export
```
